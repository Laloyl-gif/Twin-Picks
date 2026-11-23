"""Tammy Preston's Investigation (L'enquête de Tammy), façon 1jour1film : l'agente Tammy Preston ne jure que par les
données. Un film mystère, le même pour tous. Chacun propose des films sur son téléphone ; pour chaque proposition,
le rapport dit ce qu'elle a en commun avec le film mystère : genres, année (plus tôt / plus tard, proche ou non),
réalisateur, acteurs en commun (nommés), compositeur, pays, durée et note (plus / moins). Les rapports des autres
s'affichent sur l'écran, sans le titre proposé : on profite des pistes sans copier. Le premier à trouver gagne le
plus ; moins on a fait d'essais, plus on gagne.
"""
import random

from tmdb import cle_film, fiche
from visuels import en_jpeg
from .commun import affiche, cles_reponses
from .saisie_film import Saisie


def _an(fi):
    try:
        return int(fi.get("annee") or 0)
    except ValueError:
        return 0


def rapport(prop, cible):
    """Ce qu'une fiche proposée a en commun avec la fiche du film mystère."""
    r = {}
    gp, gc = set(prop.get("genres") or []), set(cible.get("genres") or [])
    r["genres"] = {"etat": "ok" if gp == gc and gc else "part" if gp & gc else "non", "communs": sorted(gp & gc)}
    ap, ac = _an(prop), _an(cible)
    if ap and ac:
        r["annee"] = {"etat": "ok" if ap == ac else "proche" if abs(ap - ac) <= 5 else "non",
                      "sens": "" if ap == ac else "↑" if ac > ap else "↓", "val": ap}
    rp = {x["id"] for x in prop.get("realisateurs", [])}
    r["real"] = {"etat": "ok" if rp & {x["id"] for x in cible.get("realisateurs", [])} else "non",
                 "noms": [x["nom"] for x in cible.get("realisateurs", []) if x["id"] in rp]}
    ids = {a["id"] for a in cible.get("acteurs", [])[:20]}
    r["acteurs"] = [a["nom"] for a in prop.get("acteurs", [])[:20] if a["id"] in ids][:4]
    cp = {x["id"] for x in prop.get("compositeurs", [])}
    r["compo"] = [x["nom"] for x in cible.get("compositeurs", []) if x["id"] in cp][:1]
    pp, pc = set(prop.get("pays") or []), set(cible.get("pays") or [])
    r["pays"] = {"etat": "ok" if pp == pc and pc else "part" if pp & pc else "non", "communs": sorted(pp & pc)}
    dp, dc = prop.get("duree") or 0, cible.get("duree") or 0
    if dp and dc:
        r["duree"] = {"etat": "ok" if abs(dp - dc) <= 10 else "non", "sens": "" if abs(dp - dc) <= 10 else "↑" if dc > dp else "↓"}
    np_, nc = prop.get("note") or 0, cible.get("note") or 0
    if np_ and nc:
        r["note"] = {"etat": "ok" if abs(np_ - nc) <= 0.3 else "non", "sens": "" if abs(np_ - nc) <= 0.3 else "↑" if nc > np_ else "↓"}
    return r


def construire(api, cfg, pool, deja):
    films = [f for f in pool if not f.get("tv") and f.get("poster_path")]
    films.sort(key=lambda f: -(f.get("votes") or 0))
    connus = films[:max(12, len(films) // 3)]
    random.shuffle(connus)
    connus.sort(key=lambda f: cle_film(f) in deja)
    for f in connus[:10]:
        try:
            fi = fiche(api, f)
        except Exception:  # noqa: BLE001
            continue
        if fi.get("genres") and fi.get("acteurs") and fi.get("realisateurs"):
            break
    else:
        raise RuntimeError("L'enquête de Tammy : pas de film assez renseigné dans les listes.")
    deja.add(cle_film(f))
    duree = float(cfg.get("dur_tammy", 150))
    return dict(jeu="tammy", vue="enquete", duree=duree, reponse="enquete", etapes=[(0.0, {})], images=[],
                revelation=en_jpeg(affiche(api, f, "w500")), cles=cles_reponses(f["title"], f.get("original_title") or ""),
                bonne=f["title"], solution=f"{f['title']} ({fi.get('annee') or '?'})", detail="", films=[cle_film(f)],
                mystere=f, mystere_fiche=fi, api=api, films_pool=pool, suggestions=True)


class Moteur:
    suggestions = True

    def __init__(self, partie, cfg, m):
        self.p, self.cfg, self.m = partie, cfg, m
        self.essais = {}                         # pid -> [rapports]
        self.trouves = []                        # pids, dans l'ordre
        self.gains = {}
        self.fil = []                            # [(pid, rapport)] pour l'écran
        self.saisie = Saisie(m["api"], m.get("films_pool", []))

    def ok(self):
        return ""

    def resoudre(self, d):
        return self.saisie.resoudre(d.get("texte"), avec_fiche=True, avec_image=False)

    def suggerer(self, q):
        return self.saisie.suggerer(q)

    def action(self, pid, d, frac, info=None):
        if pid in self.trouves:
            return {"ok": False, "msg": "Déjà trouvé !"}
        maxi = int(self.cfg.get("tammy_essais", 12))
        mes = self.essais.setdefault(pid, [])
        if len(mes) >= maxi:
            return {"ok": False, "msg": "Plus d'essais"}
        f = (info or {}).get("film")
        if not f or not (info or {}).get("fiche"):
            return {"ok": False, "msg": "Film introuvable : vérifiez le titre"}
        if any(r["cle"] == list(cle_film(f)) for r in mes):
            return {"ok": False, "msg": "Déjà proposé"}
        bon = cle_film(f) == cle_film(self.m["mystere"])
        r = {"cle": list(cle_film(f)), "titre": info["libelle"], "trouve": bon,
             "r": {} if bon else rapport(info["fiche"], self.m["mystere_fiche"])}
        mes.append(r)
        self.fil = (self.fil + [(pid, r)])[-14:]
        if bon:
            self.trouves.append(pid)
            rang = len(self.trouves) - 1
            base = [1000, 700, 500, 400, 300][min(rang, 4)]
            g = max(150, base - int(self.cfg.get("tammy_essai", 40)) * (len(mes) - 1))
            self.gains[pid] = g
            return {"ok": True, "correct": True, "msg": f"C'est lui ! +{g}"}
        return {"ok": True, "correct": False, "msg": "Rapport reçu"}

    def fini(self):
        J = self.p.joueurs
        maxi = int(self.cfg.get("tammy_essais", 12))
        return bool(J) and all(p in self.trouves or len(self.essais.get(p, [])) >= maxi for p in J)

    def clore(self):
        for pid, j in self.p.joueurs.items():
            gain = self.gains.get(pid, 0)
            j.gain += gain
            j.score += gain
            j.trouve = pid in self.trouves
            j.serie = j.serie + 1 if j.trouve else 0

    def statut(self, pid):
        if pid in self.trouves:
            return {"t": "trouvé", "c": "ok"}
        n = len(self.essais.get(pid, []))
        return {"t": f"{n} essai{'s' if n > 1 else ''}" if n else "", "c": ""}

    def avancement(self):
        return f"{len(self.trouves)} / {len(self.p.joueurs)} ont trouvé"

    def vue(self, pid, revele):
        J = self.p.joueurs
        v = {"fil": [dict(r, titre=r["titre"] if revele else None, qui=J[p].public() if p in J else None)
                     for p, r in self.fil], "maxi": int(self.cfg.get("tammy_essais", 12)),
             "trouves": [J[p].public() for p in self.trouves if p in J]}
        if pid:
            v.update(mes=self.essais.get(pid, []), trouve=pid in self.trouves,
                     actif=not revele and not self.p.pause and pid not in self.trouves and
                     len(self.essais.get(pid, [])) < v["maxi"])
        if revele:
            v["resultats"] = sorted([dict(J[p].public(), gain=self.gains.get(p, 0), essais=len(self.essais.get(p, [])))
                                     for p in J], key=lambda x: -x["gain"])
        return v
