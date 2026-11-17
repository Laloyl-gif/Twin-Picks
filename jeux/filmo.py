"""Films → Acteur : les acteurs viennent de acteurs.txt ; on prend ses 16 films les plus connus
(vrais rôles, films sortis), puis x au hasard parmi eux."""
import datetime
import random
import re

from PIL import ImageOps

from texte import est_latin
from visuels import en_jpeg
from .commun import cles_reponses, grille, horaires, tirer

PAS_UN_ROLE = re.compile(r"\b(self|himself|herself|archive|lui-même|elle-même|uncredited|non crédité|narrator|"
                         r"narrateur)\b", re.I)
ROLE_PRINCIPAL = 12          # au-delà de cette place au générique, le rôle est secondaire
PLUS_CONNUS = 16             # les films tirés au hasard viennent de ses 16 films les plus connus


def films_connus(credits, nmax):
    """Ses films les plus connus (PLUS_CONNUS, au moins 2 × nmax) où l'acteur tient un vrai rôle."""
    aujourdhui = datetime.date.today().isoformat()
    films = {}
    for c in credits:
        if not c.get("poster_path") or 99 in c.get("genre_ids", []):          # 99 = documentaire
            continue
        if not c.get("release_date") or c["release_date"] > aujourdhui:       # pas encore sorti
            continue
        if PAS_UN_ROLE.search(c.get("character") or ""):
            continue
        if c["id"] not in films or c.get("order", 99) < films[c["id"]].get("order", 99):
            films[c["id"]] = c
    tous = sorted(films.values(), key=lambda c: c.get("vote_count", 0), reverse=True)
    principaux = [c for c in tous if c.get("order", 99) <= ROLE_PRINCIPAL]
    choix = principaux if len(principaux) >= nmax else tous
    return choix[:max(PLUS_CONNUS, 2 * nmax)]


def construire(api, cfg, pool, deja):
    nmax = cfg["filmo_max"]
    for _ in range(10):
        p = tirer(pool, deja, ident=lambda a: a["id"])
        connus = films_connus(api.get(f"/person/{p['id']}/movie_credits").get("cast", []), nmax)
        if len(connus) < min(nmax, 3):
            continue
        choisis = random.sample(connus, min(nmax, len(connus)))
        affiches = api.images([f["poster_path"] for f in choisis], "w185")
        legendes = [f"{f.get('title')} ({f['release_date'][:4]})" if f.get("release_date") else f.get("title", "?")
                    for f in choisis]
        noms = [p["name"]]
        try:
            noms += [a for a in api.get(f"/person/{p['id']}").get("also_known_as", []) if est_latin(a)]
        except Exception:  # noqa: BLE001
            pass
        mots = [m for m in p["name"].split() if m.lower().strip(".,") not in ("jr", "sr", "ii", "iii")]
        if len(mots) > 1:
            noms.append(mots[-1])                         # le nom de famille seul est accepté (pas « Jr. »)
        temps = horaires(len(choisis), 1, cfg["filmo_intervalle"])
        return dict(jeu="filmo", vue="grille", duree=float(cfg["dur_filmo"]), etapes=grille(temps, legendes),
                    images=[en_jpeg(ImageOps.fit(a, (200, 300)), 300) for a in affiches],
                    revelation=en_jpeg(api.image(p["profile_path"], "h632")),
                    reponse="titre", cles=cles_reponses(*noms), bonne=p["name"], solution=p["name"])
    raise RuntimeError("Aucun acteur exploitable.")
