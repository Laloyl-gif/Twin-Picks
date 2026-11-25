"""Serveur HTTP : fichiers de l'interface web + API JSON (téléphones et écran hôte)."""
import base64
import json
import os
import re
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote, urlparse

import config
import musique
import profils
from affiches import detection as affiches_detection
from affiches.preparation import PREPARATEUR
from partie import Partie
import reseau
from reseau import Tunnel, ip_locale, qr_png
from jeux.contraintes import noms_realisateurs
from tmdb import TMDB, charger_pools, connecter, id_liste, lire_listes_compte, resoudre_liste

TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml",
         ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".ico": "image/x-icon",
         ".webmanifest": "application/manifest+json; charset=utf-8"}


def _version_icone():
    """Empreinte de l'icône : ajoutée aux liens (?v=…) pour que navigateurs et écrans d'accueil la rechargent
    dès qu'elle change, au lieu de garder l'ancienne en cache."""
    import hashlib
    try:
        with open(os.path.join(config.DOSSIER_WEB, "icone.png"), "rb") as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except OSError:
        return "0"


V_ICONE = _version_icone()
DOSSIER_PERSOS = os.path.join(config.DOSSIER_WEB, "persos")


def images_persos():
    """Images des cartes du menu : celles ajoutées depuis l'écran hôte (donnees/images_menu/) d'abord, puis celles
    fournies avec le jeu (web/persos/<perso>.jpg|jpeg|png|webp)."""
    out = {}
    try:
        for f in sorted(os.listdir(config.DOSSIER_IMAGES_MENU)):
            nom, ext = os.path.splitext(f)
            if ext.lower() == ".jpg":
                v = int(os.path.getmtime(os.path.join(config.DOSSIER_IMAGES_MENU, f)))
                out[nom.lower()] = f"/images_menu/{f}?v={v}"
    except OSError:
        pass
    try:
        fichiers = os.listdir(DOSSIER_PERSOS)
    except OSError:
        fichiers = []
    for f in sorted(fichiers):
        nom, ext = os.path.splitext(f)
        if ext.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            out.setdefault(nom.lower(), "/persos/" + f)
    return out


def image_menu(d):
    """Écran hôte › carte d'un jeu › Image : enregistre (ou retire) l'image de la carte et son petit portrait rond.
    d = {perso, data (image en base64), carte: {x, y, l, h}, portrait: {x, y, l, h}} (cadres en parts de l'image)."""
    import io
    from PIL import Image, ImageOps
    perso = re.sub(r"[^a-z0-9_]", "", str(d.get("perso", "")).lower())
    if not perso:
        raise RuntimeError("Carte inconnue.")
    carte = os.path.join(config.DOSSIER_IMAGES_MENU, perso + ".jpg")
    portrait = os.path.join(config.DOSSIER_IMAGES_MENU, "avatars", perso + ".jpg")
    if d.get("action") == "retirer":
        for f in (carte, portrait):
            try:
                os.remove(f)
            except OSError:
                pass
        return {"ok": True}
    try:
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(base64.b64decode(str(d.get("data") or "").split(",")[-1]))))
        im = im.convert("RGB")
    except (ValueError, OSError):
        raise RuntimeError("Image illisible.")

    def decouper(c, taille):
        c = c or {}
        x, y = float(c.get("x", 0)), float(c.get("y", 0))
        l, h = float(c.get("l", 1)), float(c.get("h", 1))
        boite = [round(x * im.width), round(y * im.height), round((x + l) * im.width), round((y + h) * im.height)]
        return im.crop(boite).resize(taille, Image.LANCZOS)
    os.makedirs(os.path.dirname(portrait), exist_ok=True)
    decouper(d.get("carte"), (900, 474)).save(carte, quality=88)
    decouper(d.get("portrait"), (256, 256)).save(portrait, quality=88)
    return {"ok": True}


class App:
    """Relie les réglages, la partie, le tunnel et les actions de l'écran hôte."""

    def __init__(self, type_="ordinateur", reprise=None):
        self.type = type_                                  # « ordinateur » ou « telephone » (application Android)
        self.reglages = config.charger()
        self.partie = Partie()
        self.snap_json, self.snap_v, self._etait_en_cours = None, "", False
        self.jeton = secrets.token_urlsafe(12)            # clé de l'écran hôte
        self.verrou = threading.Lock()
        self.tunnel, self.tunnel_etat, self.url_locale = Tunnel(config.PORT), "", ""
        self.code = self._code_salle()                     # le code de la partie (le même d'un lancement à l'autre)
        self.vu_ecran = 0.0                                # dernier passage d'un écran de partie (pas un téléphone)
        self.salle_publiee = False
        self._qr = (None, None)
        self._sig_affiches = None                         # dernière préparation automatique lancée
        threading.Thread(target=self._surveiller_affiches, daemon=True).start()
        if reprise:                                       # l'hôte s'est éteint : ce téléphone reprend la partie
            self.code = reseau.normaliser_code(reprise.get("code") or "") or self.code
            self.partie.restaurer(reprise)
        threading.Thread(target=self._sauvegarder, daemon=True).start()

    def definir_port(self, port):
        self.url_locale = f"http://{ip_locale()}:{port}"
        self.tunnel = Tunnel(port)
        threading.Thread(target=self._salle, daemon=True).start()

    # ---------- sauvegarde continue, reprise ----------
    FICHIER_REPRISE = config.donnee("reprise.json")

    def _sauvegarder(self):
        """Toutes les 3 s : la partie en cours est sauvegardée (donnees/reprise.json) si elle a changé, et gardée
        pour les téléphones de l'application, qui la reprennent si cet appareil s'éteint. Partie finie, ou retour
        volontaire au menu : la sauvegarde est effacée."""
        import hashlib
        while True:
            time.sleep(3)
            try:
                snap = self.partie.instantane(self.code)
                if snap:
                    snap["relais"] = self.relais()
                    corps = json.dumps({k: v for k, v in snap.items() if k != "quand"}, ensure_ascii=False,
                                       sort_keys=True, default=list)
                    v = hashlib.md5(corps.encode()).hexdigest()[:12]
                    if v != self.snap_v:
                        self.snap_json, self.snap_v = json.dumps(snap, ensure_ascii=False, default=list), v
                        with open(self.FICHIER_REPRISE + ".tmp", "w", encoding="utf-8") as f:
                            f.write(self.snap_json)
                        os.replace(self.FICHIER_REPRISE + ".tmp", self.FICHIER_REPRISE)
                    self._etait_en_cours = True
                elif self._etait_en_cours and self.partie.phase in ("lobby", "fin"):
                    self._etait_en_cours, self.snap_json, self.snap_v = False, None, ""
                    self.oublier_reprise()
            except Exception:  # noqa: BLE001
                import traceback
                traceback.print_exc()

    def reprise_dispo(self):
        """La partie interrompue (plantage, coupure) qu'on peut reprendre depuis le menu : résumé, ou None."""
        if self.partie.en_cours():
            return None
        try:
            mt = os.path.getmtime(self.FICHIER_REPRISE)
            if getattr(self, "_reprise_cache", (None,))[0] == mt:
                return self._reprise_cache[1]
            with open(self.FICHIER_REPRISE, encoding="utf-8") as f:
                snap = json.load(f)
        except (OSError, ValueError):
            return None
        if time.time() - snap.get("quand", 0) > 12 * 3600:
            return None
        js = sorted(snap.get("joueurs", []), key=lambda j: -j.get("score", 0))
        res = {"manche": snap.get("index", 0) + 1, "total": len(snap.get("plan", [])),
               "quand": time.strftime("%H:%M", time.localtime(snap.get("quand", 0))),
               "joueurs": [{"nom": j["nom"], "score": j["score"], "couleur": j["couleur"]} for j in js]}
        self._reprise_cache = (mt, res)
        return res

    def reprendre(self):
        try:
            with open(self.FICHIER_REPRISE, encoding="utf-8") as f:
                snap = json.load(f)
        except (OSError, ValueError):
            return "Aucune partie à reprendre."
        return self.partie.restaurer(snap)

    def oublier_reprise(self):
        try:
            os.remove(self.FICHIER_REPRISE)
        except OSError:
            pass

    def relais(self):
        """Les téléphones de l'application qui peuvent reprendre la partie si cet appareil s'éteint (adresses)."""
        out = []
        for j in list(self.partie.joueurs.values()):
            ip = getattr(j, "ip_appli", "")
            if ip and not ip.startswith("127.") and f"http://{ip}:{config.PORT}" not in out:
                out.append(f"http://{ip}:{config.PORT}")
        return out

    # ---------- code de la partie ----------
    @staticmethod
    def _code_salle():
        fichier = config.donnee("salle.json")
        try:
            with open(fichier, encoding="utf-8") as f:
                code = reseau.normaliser_code(json.load(f).get("code", ""))
            if len(code) >= 4:
                return code
        except (OSError, ValueError):
            pass
        code = reseau.nouveau_code()
        try:
            with open(fichier, "w", encoding="utf-8") as f:
                json.dump({"code": code}, f)
        except OSError:
            pass
        return code

    def publier_salle(self):
        try:
            reseau.publier_salle(self.code, {"lan": self.url_locale, "net": self.tunnel.url or "", "type": self.type})
            self.salle_publiee = True
        except Exception:  # noqa: BLE001  (hors ligne : le code ne marchera que sur ce Wi-Fi)
            self.salle_publiee = False

    def _salle(self):
        """Au lancement : le code est publié (adresse Wi-Fi), puis le tunnel Internet s'ouvre tout seul et le code
        est republié avec l'adresse Internet. Republié toutes les 6 h (le relais garde 12 h)."""
        import time
        self.publier_salle()
        if self.reglages.get("salle_internet", True) and not self.tunnel.url:
            self.basculer_tunnel()
        while True:
            time.sleep(6 * 3600)
            self.publier_salle()

    def rejoindre_salle(self, code):
        code = reseau.normaliser_code(code)
        if code == self.code:
            return {"lan": self.url_locale, "net": self.tunnel.url or "", "ici": True}
        try:
            infos = reseau.resoudre_salle(code)
        except Exception:  # noqa: BLE001
            raise RuntimeError("Impossible de chercher la partie : pas d'Internet ?")
        if not infos:
            raise RuntimeError(f"Aucune partie avec le code {code}.")
        return infos

    @property
    def url(self):
        return self.tunnel.url or self.url_locale

    def qr(self):
        if self._qr[0] != self.url:
            self._qr = (self.url, qr_png(self.url))
        return self._qr[1]

    def api(self):
        r = self.reglages
        return TMDB(r["api_key"], r["session_id"], r["account_id"])

    # ---------- réglages ----------
    def maj_reglages(self, brut):
        with self.verrou:
            self.reglages = config.valider(brut, self.reglages)
            config.sauver(self.reglages)

    def config_hote(self):
        r = {k: v for k, v in self.reglages.items() if k != "session_id"}
        return dict(reglages=r, params=config.PARAMS, groupes=config.GROUPES, jeux=config.JEUX,
                    modes=config.MODES_REPONSE, couleurs=config.COULEURS, persos=images_persos(),
                    compte=self.reglages["account_name"] if self.reglages["session_id"] else "",
                    profils=self.profils_resumes(), avatars=config.avatars(),
                    realisateurs=noms_realisateurs(self.reglages), type=self.type)

    def profils_resumes(self):
        return [profils.resume(p, self.reglages["listes_connues"]) for p in profils.charger()]

    def profils(self, d):
        """Gestion des profils depuis l'écran hôte (ajout, listes, import d'un fichier…)."""
        a, connues = d.get("action"), self.reglages["listes_connues"]
        if a == "importer":
            try:
                data = base64.b64decode(str(d.get("data") or "").split(",")[-1])
            except ValueError:
                raise RuntimeError("Fichier illisible.")
            if not data:
                raise RuntimeError("Fichier vide.")
            r = profils.importer(self.api(), str(d.get("id") or ""), str(d.get("nom_fichier") or ""), data, connues)
            return {"profils": r["profils"], "msg": r["msg"]}
        if a in ("ajouter", "supprimer", "renommer", "avatar", "listes", "vider", "realisateurs"):
            res = profils.modifier(a, d, connues)
            if a == "ajouter" and d.get("data"):
                nouveau = next((p for p in res if p["nom"] == " ".join(str(d.get("nom")).split())[:16]), None)
                if nouveau:
                    return self.profils(dict(d, action="importer", id=nouveau["id"]))
            return {"profils": res}
        return {"profils": self.profils_resumes()}

    def etat_hote(self):
        v = self.partie.vue_hote()
        v.update(url=self.url, en_ligne=bool(self.tunnel.url), tunnel=self.tunnel_etat, code=self.code,
                 reprise=self.reprise_dispo() if v.get("phase") in ("lobby", "fin") else None,
                 profils_actifs=self.partie.profils_presents() if self.reglages["profils_auto"] else [],
                 profils_presents=self.partie.profils_presents(),
                 affiches=PREPARATEUR.etat())
        return v

    # ---------- affiches vidées (Pete) ----------
    def _signature_affiches(self):
        """Ce dont dépendent les affiches à préparer : listes de Pete, profils présents, options d'effacement."""
        r = self.reglages
        l = r["listes"]["pete"]
        noms = tuple(sorted(self.partie.profils_presents())) if r["profils_auto"] else ()
        return (tuple(sorted(l["inc"])), tuple(sorted(l["exc"])), tuple(sorted(l.get("plus", []))), noms, r["pete_textes"], r["pete_personnages"],
                r["pete_objets"], r["pete_ordre"])

    def _surveiller_affiches(self):
        """Préparation automatique : dès qu'une liste de Pete est incluse ou qu'un joueur arrive avec un profil,
        toutes les affiches des films concernés sont préparées (celles qui existent déjà sont réutilisées)."""
        import time
        time.sleep(2)
        while True:
            try:
                r = self.reglages
                sig = self._signature_affiches()
                if r["pete_auto"] and (sig[0] or sig[3]) and sig != self._sig_affiches:
                    if PREPARATEUR.actif():
                        if PREPARATEUR.signature is not None:     # préparation automatique dépassée : on l'arrête
                            PREPARATEUR.arreter()
                    else:
                        self._sig_affiches = sig
                        self._lancer_affiches(sig)
            except Exception:  # noqa: BLE001
                pass
            time.sleep(3)

    def _lancer_affiches(self, signature=None):
        r, api, connues = self.reglages, self.api(), self.reglages["listes_connues"]
        presents = []
        if r["profils_auto"]:
            noms = set(self.partie.profils_presents())
            presents = [profils.pour_partie(p, connues) for p in profils.charger() if p["nom"] in noms]

        def lancer():
            try:
                pools, _ = charger_pools(api, r, {"pete"}, presents)
                PREPARATEUR.lancer(api, pools["films_pete"],
                                   {"textes": r["pete_textes"], "personnages": r["pete_personnages"],
                                    "objets": r["pete_objets"]}, r["pete_ordre"], signature=signature)
            except Exception as err:  # noqa: BLE001
                erreur = re.sub(r"\?\S*", "", str(err))[:200]          # sans la clé API ni la session
                PREPARATEUR._maj(erreur=erreur, message="Impossible de lire les films de Pete (connexion à TMDB ?).")

        PREPARATEUR._maj(message="Lecture des films de Pete…", erreur="")
        threading.Thread(target=lancer, daemon=True).start()

    def affiches(self, d):
        """Préparer / arrêter la préparation des affiches vidées depuis l'écran hôte."""
        a = d.get("action")
        if a == "arreter":
            PREPARATEUR.arreter()
        elif a == "outils":
            return {"outils": affiches_detection.outils_disponibles(), "etat": PREPARATEUR.etat()}
        elif a == "preparer" and not PREPARATEUR.actif():
            sig = self._signature_affiches()
            self._sig_affiches = sig
            self._lancer_affiches(sig)
        return {"etat": PREPARATEUR.etat()}

    # ---------- actions ----------
    def action(self, d):
        a, p = d.get("action"), self.partie
        if a == "lancer":
            return {"erreur": p.demarrer(self.reglages, self.reglages["listes_connues"])}
        if a == "pause":
            p.basculer_pause()
        elif a == "passer":
            p.passer()
        elif a == "rejouer":
            p.rejouer()
        elif a == "menu":
            p.menu()
        elif a == "reprendre":
            return {"erreur": self.reprendre()}
        elif a == "oublier_reprise":
            self.oublier_reprise()
        elif a == "exclure":
            p.exclure(str(d.get("id", "")))
        elif a == "tunnel":
            self.basculer_tunnel()
        return {}

    def basculer_tunnel(self):
        if self.tunnel_etat == "connexion":
            return
        if self.tunnel.url:
            self.tunnel.arreter()
            return
        self.tunnel_etat = "connexion"

        def ouvrir():
            try:
                self.tunnel.demarrer()
                self.tunnel_etat = ""
            except Exception as err:  # noqa: BLE001
                self.tunnel_etat = "erreur:" + str(err)
            self.publier_salle()                          # le code mène maintenant aussi par Internet

        threading.Thread(target=ouvrir, daemon=True).start()

    def _fusionner(self, listes, **compte):
        connues = {l["id"]: l for l in self.reglages["listes_connues"]}
        for l in listes:
            connues[l["id"]] = l
        self.maj_reglages(dict(listes_connues=list(connues.values()), **compte))

    def tmdb(self, d):
        a, api = d.get("action"), self.api()
        if a == "token":
            jeton = api.get("/authentication/token/new")["request_token"]
            return {"token": jeton, "url": f"https://www.themoviedb.org/authenticate/{jeton}"}
        if a == "session":
            data = connecter(api, str(d.get("token", "")))
            self._fusionner(data["listes"], session_id=data["session_id"],
                            account_id=data["compte"], account_name=data["nom"])
        elif a == "actualiser":
            if not self.reglages["session_id"]:
                raise RuntimeError("Connectez d'abord votre compte TMDB.")
            data = lire_listes_compte(api, self.reglages["session_id"])
            self._fusionner(data["listes"], account_id=data["compte"],
                            account_name=data["nom"] or self.reglages["account_name"])
        elif a == "deconnecter":
            self.maj_reglages({"session_id": "", "account_id": 0, "account_name": ""})
        elif a == "ajouter":
            lid = id_liste(d.get("texte", ""))
            if lid is None:
                raise RuntimeError("Entrez un numéro de liste ou un lien TMDB.")
            self._fusionner([resoudre_liste(api, lid)])
            jeu = d.get("jeu")
            if jeu in self.reglages["listes"]:
                s = self.reglages["listes"][jeu]
                cle = "plus" if d.get("plus") else "inc"            # profils présents : ajoutée aux films vus
                self.maj_reglages({"listes": {jeu: {cle: s.get(cle, []) + ([] if lid in s.get(cle, []) else [lid]),
                                                    "exc": [i for i in s["exc"] if i != lid]}}})
        return self.config_hote()


def fabriquer_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _envoyer(self, data, type_="application/json; charset=utf-8", code=200, cache="no-store", entetes=None):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False).encode("utf-8")
            try:
                self.send_response(code)
                self.send_header("Content-Type", type_)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", cache)
                for k, val in (entetes or {}).items():
                    self.send_header(k, val)
                self.end_headers()
                self.wfile.write(data)
            except (ConnectionError, OSError):
                pass

        def _fichier(self, nom, dossier=config.DOSSIER_WEB, cache="no-store"):
            nom = os.path.basename(nom)
            try:
                with open(os.path.join(dossier, nom), "rb") as f:
                    data = f.read()
            except OSError:
                return self.send_error(404)
            ext = os.path.splitext(nom)[1].lower()
            if ext in (".html", ".webmanifest"):
                data = data.replace(b"__VICONE__", V_ICONE.encode())
            self._envoyer(data, TYPES.get(ext, "application/octet-stream"), cache=cache)

        def _flux(self, chemin, mime):
            """Fichier audio envoyé par morceaux, avec prise en charge de « Range » (avance rapide, reprise)."""
            try:
                taille = os.path.getsize(chemin)
                debut, fin, code = 0, taille - 1, 200
                m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range") or "")
                if m and (m.group(1) or m.group(2)):
                    if m.group(1):
                        debut = int(m.group(1))
                        fin = min(taille - 1, int(m.group(2))) if m.group(2) else taille - 1
                    else:
                        debut = max(0, taille - int(m.group(2)))
                    if debut > fin:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{taille}")
                        self.end_headers()
                        return
                    code = 206
                self.send_response(code)
                self.send_header("Content-Type", mime)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(fin - debut + 1))
                self.send_header("Cache-Control", "private, max-age=3600")
                if code == 206:
                    self.send_header("Content-Range", f"bytes {debut}-{fin}/{taille}")
                self.end_headers()
                with open(chemin, "rb") as f:
                    f.seek(debut)
                    reste = fin - debut + 1
                    while reste > 0:
                        bloc = f.read(min(1 << 16, reste))
                        if not bloc:
                            break
                        self.wfile.write(bloc)
                        reste -= len(bloc)
            except (ConnectionError, OSError):
                pass

        def _hote(self, q):
            return secrets.compare_digest(q.get("k", [""])[0].encode(), app.jeton.encode())

        def do_GET(self):
            u = urlparse(self.path)
            q, c, p = parse_qs(u.query), u.path, app.partie
            if c in ("/", "/index.html"):
                return self._fichier("joueur.html")
            if c == "/hote":
                return self._fichier("hote.html")
            if c == "/favicon.ico":
                return self._fichier("icone.ico", cache="no-cache")
            if c == "/manifest.webmanifest":
                return self._fichier("manifest.webmanifest", cache="no-cache")
            if c.startswith("/web/"):
                return self._fichier(c[5:])
            if c.startswith("/persos/avatars/"):
                perso = os.path.join(config.DOSSIER_IMAGES_MENU, "avatars", os.path.basename(unquote(c[16:])))
                if os.path.isfile(perso):                   # portrait choisi depuis l'écran hôte
                    return self._fichier(perso, os.path.dirname(perso), cache="no-cache")
                return self._fichier(unquote(c[16:]), config.DOSSIER_AVATARS, cache="no-cache")
            if c.startswith("/images_menu/"):
                return self._fichier(unquote(c[13:]), config.DOSSIER_IMAGES_MENU, cache="public, max-age=86400")
            if c.startswith("/persos/"):
                return self._fichier(unquote(c[8:]), DOSSIER_PERSOS)
            if c.startswith("/audio/"):
                data = p.audio(c[7:], self._hote(q))
                return self._envoyer(data, "audio/mpeg") if data else self.send_error(404)
            if c.startswith("/musique/l") and self._hote(q):  # morceau complet du dossier musique/
                chemin, mime = musique.fichier_local(c[9:])
                return self._flux(chemin, mime) if chemin else self.send_error(404)
            if c.startswith("/musique/"):                     # musique d'ambiance : écran hôte seulement
                ident = c[9:]
                data = musique.mp3(int(ident)) if self._hote(q) and ident.isdigit() else None
                return self._envoyer(data, "audio/mpeg", cache="private, max-age=600") if data else self.send_error(404)
            if c == "/api/etat":
                pid = q.get("pid", [""])[0]
                p.reclamer(pid)
                j = p.joueurs.get(pid)
                if j and "TwinPicksApp" in (self.headers.get("User-Agent") or ""):
                    j.ip_appli = self.client_address[0]       # téléphone de l'application : relais possible
                v = p.vue_joueur(pid)
                if j and p.en_cours():                          # où aller si cet appareil s'éteint
                    v["relais"], v["code"] = app.relais(), app.code
                return self._envoyer(v)
            if c == "/api/salle":                               # lisible depuis une autre partie (relais)
                return self._envoyer({"code": app.code, "internet": bool(app.tunnel.url),
                                      "en_cours": p.en_cours()}, entetes={"Access-Control-Allow-Origin": "*"})
            if c == "/api/reprise":
                # la sauvegarde, pour les téléphones de l'application seulement (reconnus à leur adresse)
                ip = self.client_address[0]
                if not any(getattr(j, "ip_appli", "") == ip for j in list(p.joueurs.values())):
                    return self._envoyer({"interdit": True}, code=403)
                if not app.snap_json:
                    return self._envoyer({"aucune": True})
                if q.get("v", [""])[0] == app.snap_v:
                    return self._envoyer({"meme": True, "v": app.snap_v})
                return self._envoyer(('{"v": "%s", "snap": %s}' % (app.snap_v, app.snap_json)).encode("utf-8"))
            if c == "/api/couleurs":
                return self._envoyer(p.couleurs())
            if c == "/api/suggestions":
                return self._envoyer(p.suggestions(q.get("q", [""])[0]))
            if c.startswith("/img/"):
                morceaux = c.split("/")
                data = p.image(morceaux[2], morceaux[3], self._hote(q)) if len(morceaux) == 4 else None
                if data:
                    return self._envoyer(data, "image/jpeg", cache="private, max-age=600")
                return self.send_error(404)
            if c.startswith("/api/hote/") or c == "/qr.png":
                if not self._hote(q):
                    return self._envoyer({"interdit": True}, code=403)
                if c == "/api/hote/etat":
                    if "tel" not in q:
                        app.vu_ecran = time.monotonic()
                    return self._envoyer(dict(app.etat_hote(), ecran_actif=time.monotonic() - app.vu_ecran < 6))
                if c == "/api/hote/config":
                    return self._envoyer(app.config_hote())
                if c == "/api/hote/historique":
                    import historique
                    return self._envoyer({"parties": historique.liste()})
                if c == "/api/hote/palmares":
                    import palmares
                    return self._envoyer(palmares.resume())
                if c == "/api/hote/musique":
                    sauf = [int(x) if x.isdigit() else x for x in q.get("sauf", [""])[0].split(",") if x]
                    return self._envoyer({"piste": musique.piste_aleatoire(q.get("genre", ["jeu"])[0], sauf,
                                                                           app.partie, app.reglages)})
                if c == "/api/hote/profils":
                    return self._envoyer({"profils": app.profils_resumes()})
                if c == "/qr.png":
                    png = app.qr()
                    return self._envoyer(png, "image/png") if png else self.send_error(404)
            self.send_error(404)

        def do_POST(self):
            u = urlparse(self.path)
            q, p = parse_qs(u.query), app.partie
            try:
                n = int(self.headers.get("Content-Length", 0))
                d = json.loads(self.rfile.read(n) or b"{}")
                d = d if isinstance(d, dict) else {}
            except (ValueError, OSError):
                d = {}
            pid = str(d.get("pid", ""))
            p.reclamer(pid)
            joueur = {
                "/api/rejoindre": lambda: {"pid": p.rejoindre(d.get("nom", ""), d.get("couleur", ""),
                                                              str(d.get("avatar") or ""),
                                                              None if d.get("profil") is None else str(d["profil"]))},
                "/api/profil": lambda: p.profil(pid, d.get("nom"), d.get("couleur"),
                                                None if d.get("avatar") is None else str(d.get("avatar")),
                                                None if d.get("profil") is None else str(d["profil"])),
                "/api/quitter": lambda: p.quitter(pid),
                "/api/repondre": lambda: p.repondre(pid, str(d.get("texte", "")), {"case": d.get("case")}),
                "/api/jouer": lambda: p.jouer(pid, {k: v for k, v in d.items() if k != "pid"}),
                "/api/choisir": lambda: p.choisir(pid, d.get("i")),
                "/api/buzz": lambda: p.buzz(pid),
                "/api/salle/rejoindre": lambda: app.rejoindre_salle(d.get("code", "")),
            }
            hote = {
                "/api/hote/reglages": lambda: (app.maj_reglages(d), app.config_hote())[1],
                "/api/hote/action": lambda: app.action(d),
                "/api/hote/tmdb": lambda: app.tmdb(d),
                "/api/hote/profils": lambda: app.profils(d),
                "/api/hote/affiches": lambda: app.affiches(d),
                "/api/hote/image_menu": lambda: (image_menu(d), app.config_hote())[1],
            }
            try:
                if u.path in joueur:
                    return self._envoyer(joueur[u.path]())
                if u.path in hote:
                    if not self._hote(q):
                        return self._envoyer({"interdit": True}, code=403)
                    return self._envoyer(hote[u.path]())
            except Exception as err:  # noqa: BLE001
                return self._envoyer({"erreur": str(err)})
            self.send_error(404)

    return Handler
