"""Images : JPEG pour le réseau, étapes d'effets (de la plus déformée à la plus lisible)."""
import io
import random
import threading

from PIL import Image, ImageFilter

try:
    import effets
    import effets_plus  # noqa: F401  (ajoute ses effets aux familles de effets.py)
except ImportError:
    effets = None

VERROU = threading.Lock()          # les effets utilisent le générateur aléatoire global


def en_jpeg(img, cote=800, qualite=85):
    img = img.copy()
    img.thumbnail((cote, cote), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=qualite)
    return buf.getvalue()


def _simple(orig, s, pos):
    """Effets de secours (zoom + pixels + flou) si effets.py est absent."""
    if s <= 0:
        return orig
    w, h = orig.size
    f = 1 - 0.7 * s
    cw, ch = max(30, int(w * f)), max(45, int(h * f))
    x, y = int((w - cw) * pos[0]), int((h - ch) * pos[1])
    im = orig.crop((x, y, x + cw, y + ch)).resize((w, h), Image.Resampling.BILINEAR)
    b = 1 + int(s * 20)
    im = im.resize((max(1, w // b), max(1, h // b)), Image.Resampling.BILINEAR).resize((w, h), Image.Resampling.NEAREST)
    return im.filter(ImageFilter.GaussianBlur(s * 6))


def etapes_effets(orig, nb_effets, puissance_max, etapes, final=0.0):
    """Liste d'images : mêmes effets, de moins en moins forts, jusqu'à puissance_max × final.
    La puissance décroît en ligne droite (puissances non arrondies : pas de paliers)."""
    etapes = max(2, int(etapes))
    puissances = [puissance_max * (1 - (1 - final) * k / (etapes - 1)) for k in range(etapes)]
    pos = (random.random(), random.random())
    if effets is None:
        return [_simple(orig, q / 10, pos) for q in puissances]
    graine = random.randrange(1 << 30)
    with VERROU:
        etat = random.getstate()
        try:
            # 1) tirage des effets sur une miniature (rapide) : on ne garde que leurs noms
            mini = orig.copy()
            mini.thumbnail((200, 200))
            _, noms = effets.transformer_image(mini, nb_effets, puissance_max, graine=graine, retourner_noms=True)
            fonctions = {f.__name__: f for liste in (effets.EFFETS_DEFORMATION, effets.EFFETS_COULEUR,
                                                     effets.EFFETS_COMPLEMENTAIRES) for f in liste}
            rendus = {}

            def rendre(p):
                # 2) chaque effet reçoit toujours la même graine : mêmes effets, puissance différente
                if p not in rendus:
                    im = orig
                    for nom in noms:
                        random.seed(f"{graine}-{nom}")
                        try:
                            im2 = fonctions[nom](im, p)
                        except TypeError:          # effet qui n'accepte qu'une puissance entière
                            random.seed(f"{graine}-{nom}")
                            im2 = fonctions[nom](im, max(1, int(round(p))))
                        im = im2
                        if im.size != orig.size:
                            im = im.resize(orig.size, Image.Resampling.BILINEAR)
                    rendus[p] = im.convert("RGB")
                return rendus[p]

            out = []
            for q in puissances:
                if q >= 1:
                    out.append(rendre(round(min(10.0, q), 2)))
                elif q <= 0:
                    out.append(orig)
                else:                       # sous la puissance 1 : fondu vers l'original
                    out.append(Image.blend(rendre(1), orig, 1 - q))
            return out
        except Exception:  # noqa: BLE001
            return [_simple(orig, q / 10, pos) for q in puissances]
        finally:
            random.setstate(etat)
