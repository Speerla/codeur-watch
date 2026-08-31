# -*- coding: utf-8 -*-
"""kit.py — le dossier de départ d'une maquette Codeur, en une commande.

Le pari de la chaîne : arriver sur un projet avec la maquette déjà construite et
en ligne pendant que les autres écrivent leur devis. Ce qui coûtait du temps
n'était pas la maquette, c'était tout ce qu'il y a autour : lire le brief,
retrouver le site du client, le mesurer, relever ses couleurs, récupérer son
logo. Ce script fait tout ça et laisse la seule chose qui doit rester à la main :
la page elle-même.

    python kit.py 488950
    python kit.py https://www.codeur.com/projects/488950-gestion-de-teleprospection
    python kit.py --site exemple.fr --nom "Atelier Martin"

Sort dans kits/<id-slug>/ :
    DOSSIER.md     les faits, les constats mesurés, ce qui est prouvé ou non
    identite.json  palette, polices, logo, images du client
    medias/        le logo et les images téléchargés, prêts à être repris

Aucune dépendance, bibliothèque standard uniquement.
"""

import argparse
import html as H
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone

try:
    import probe  # mesure du site, déjà écrit pour la veille
except ImportError:
    probe = None

try:
    import directions  # une direction visuelle par métier
except ImportError:
    directions = None

try:
    import dispositifs  # ce qui a déjà servi, donc ce qui est interdit
except ImportError:
    dispositifs = None

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.join(HERE, "kits")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

# gris, blancs et noirs : présents partout, ne disent rien d'une marque
def _est_neutre(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    return (mx - mn) < 26 or mx < 26 or mn > 235


def _get(url, delai=20, max_octets=3_000_000):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
    with urllib.request.urlopen(req, timeout=delai) as r:
        return r.geturl(), r.read(max_octets)


def _texte(url, **kw):
    try:
        final, brut = _get(url, **kw)
        return final, brut.decode("utf-8", errors="replace")
    except Exception:
        return url, ""


# --------------------------------------------------------------------------- #
# Le projet Codeur
# --------------------------------------------------------------------------- #

def projet(ref):
    """Tout ce que la page publique d'un projet donne, sans abonnement."""
    if ref.isdigit():
        ref = f"https://www.codeur.com/projects/{ref}"
    final, h = _texte(ref)
    if not h:
        sys.exit(f"Projet injoignable : {ref}")

    def prem(motif, defaut=""):
        m = re.search(motif, h, re.I | re.S)
        return H.unescape(re.sub(r"\s+", " ", m.group(1)).strip()) if m else defaut

    brief = prem(r'<meta name="description" content="([^"]{0,600})')
    offres = prem(r"(\d+)\s+offres?\s")
    budget = prem(r'Budget indicatif[^>]*>\s*([^<]{0,60})')
    titre = prem(r"<title>([^<|]{0,120})")

    return {
        "url": final,
        "id": (re.search(r"/projects/(\d+)", final) or [None, ""])[1],
        "titre": titre.strip(" -·|"),
        "budget": re.sub(r"\s+", " ", budget).strip(),
        "offres_deja": int(offres) if offres.isdigit() else None,
        "brief": brief,
        "releve_le": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
    }


# --------------------------------------------------------------------------- #
# L'identité visuelle du client, relevée sur son site
# --------------------------------------------------------------------------- #

def feuilles_css(html, base):
    """Le CSS du site : les blocs <style> et les feuilles liées."""
    morceaux = re.findall(r"<style[^>]*>(.*?)</style>", html, re.I | re.S)
    liens = re.findall(
        r'<link[^>]*rel=["\']?stylesheet["\']?[^>]*href=["\']([^"\']+)', html, re.I)
    liens += re.findall(
        r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']?stylesheet', html, re.I)
    for href in liens[:6]:
        _, css = _texte(urllib.parse.urljoin(base, href), max_octets=900_000)
        if css:
            morceaux.append(css)
    return "\n".join(morceaux)


def palette(css, html):
    """Les couleurs de marque, par fréquence, neutres écartées."""
    source = css + " " + html
    trouvees = Counter()

    for hexa in re.findall(r"#([0-9a-fA-F]{6})\b", source):
        r, g, b = (int(hexa[i:i + 2], 16) for i in (0, 2, 4))
        if not _est_neutre(r, g, b):
            trouvees["#" + hexa.lower()] += 1
    for rr, gg, bb in re.findall(r"rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)", source):
        r, g, b = int(rr), int(gg), int(bb)
        if not _est_neutre(r, g, b):
            trouvees["#%02x%02x%02x" % (r, g, b)] += 1
    for ok in re.findall(r"oklch\(([^)]{5,40})\)", source):
        trouvees["oklch(%s)" % re.sub(r"\s+", " ", ok.strip())] += 1

    return [{"couleur": c, "occurrences": n} for c, n in trouvees.most_common(8)]


def polices(css, html):
    """Les familles réellement déclarées, hors piles système."""
    generiques = {"sans-serif", "serif", "monospace", "system-ui", "inherit",
                  "cursive", "fantasy", "ui-monospace", "-apple-system",
                  "blinkmacsystemfont", "segoe ui", "roboto", "helvetica neue",
                  "arial", "helvetica", "sans", "initial", "unset", "revert"}
    vues = Counter()
    for decl in re.findall(r"font-family\s*:\s*([^;}\"']+)", css + " " + html, re.I):
        for nom in decl.split(","):
            nom = nom.strip().strip("\"'")
            if nom and nom.lower() not in generiques and len(nom) < 40:
                vues[nom] += 1
    for href in re.findall(r"fonts\.googleapis\.com/css2?\?([^\"']+)", html, re.I):
        for fam in re.findall(r"family=([A-Za-z0-9+ ]+)", href):
            vues[fam.replace("+", " ")] += 5  # une police chargée exprès compte double
    return [{"police": p, "occurrences": n} for p, n in vues.most_common(6)]


def visuels(html, base):
    """Le logo probable, et les images les plus grandes de la page d'accueil."""
    logo = ""
    for motif in (r'<link[^>]*rel=["\'][^"\']*apple-touch-icon[^"\']*["\'][^>]*href=["\']([^"\']+)',
                  r'<img[^>]*(?:class|id|alt|src)=["\'][^"\']*logo[^"\']*["\'][^>]*src=["\']([^"\']+)',
                  r'<img[^>]*src=["\']([^"\']*logo[^"\']*)["\']',
                  r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)'):
        m = re.search(motif, html, re.I)
        if m:
            logo = urllib.parse.urljoin(base, H.unescape(m.group(1)))
            break

    images, vues = [], set()
    for src in re.findall(r'<img[^>]*src=["\']([^"\']+)', html, re.I):
        if src.startswith("data:"):
            continue
        u = urllib.parse.urljoin(base, H.unescape(src))
        if u not in vues and u != logo:
            vues.add(u)
            images.append(u)
    return logo, images[:10]


def telecharge(urls, dossier):
    os.makedirs(dossier, exist_ok=True)
    gardes = []
    for u in urls:
        if not u:
            continue
        nom = re.sub(r"[^a-zA-Z0-9._-]", "_", urllib.parse.urlparse(u).path.rsplit("/", 1)[-1])
        nom = (nom or "image")[:60]
        try:
            _, data = _get(u, delai=15, max_octets=6_000_000)
        except Exception:
            continue
        if len(data) < 900:  # pixels de suivi, spacers
            continue
        chemin = os.path.join(dossier, nom)
        with open(chemin, "wb") as f:
            f.write(data)
        gardes.append({"url": u, "fichier": os.path.relpath(chemin, HERE),
                       "octets": len(data)})
    return gardes


# Pages de parking et de chantier : ce qu'on y relève appartient à l'hébergeur,
# pas au client. Les présenter comme sa marque serait un faux constat.
CHANTIER = [
    ("__ovh/", "page de chantier OVH"),
    ("site en construction", "page « Site en construction »"),
    ("bientôt disponible", "page d'attente"),
    ("coming soon", "page « coming soon »"),
    ("parking", "page de parking de registrar"),
    ("domaine a bien été créé", "page de bienvenue de registrar"),
    ("default web page", "page par défaut du serveur"),
    ("it works!", "page par défaut Apache"),
    ("welcome to nginx", "page par défaut nginx"),
]


def page_de_chantier(html, url):
    """Renvoie la raison si la page n'appartient pas vraiment au client."""
    bas = (html[:20000] + " " + url).lower()
    for marqueur, raison in CHANTIER:
        if marqueur in bas:
            return raison
    return None


def identite(domaine):
    """Ce qu'on peut relever de la marque du client, sur son propre site."""
    base = domaine if domaine.startswith("http") else "https://" + domaine
    final, html = _texte(base)
    if not html:
        final, html = _texte(base.replace("https://", "http://", 1))
    if not html:
        return None

    chantier = page_de_chantier(html, final)
    if chantier:
        return {"url": final, "chantier": chantier, "palette": [], "polices": [],
                "logo": "", "images": [], "titre_page": ""}

    css = feuilles_css(html, final)
    logo, images = visuels(html, final)
    return {
        "url": final,
        "palette": palette(css, html),
        "polices": polices(css, html),
        "logo": logo,
        "images": images,
        "titre_page": H.unescape(
            (re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S) or [None, ""])[1].strip()),
    }


# --------------------------------------------------------------------------- #
# Le dossier
# --------------------------------------------------------------------------- #

def dossier_md(p, mesure, ident, nom):
    L = []
    a = L.append
    a(f"# {nom}, kit de maquette")
    a("")
    a(f"Relevé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}. "
      "Tout ce qui suit est mesuré ou recopié, rien n'est déduit.")
    a("")

    if p:
        a("## Le projet Codeur")
        a("")
        a("| | |")
        a("|---|---|")
        a(f"| Projet | [{p['titre']}]({p['url']}) |")
        a(f"| Budget annoncé | {p['budget'] or 'non affiché'} |")
        offres = p["offres_deja"]
        a(f"| Offres déjà reçues | **{offres if offres is not None else '?'}** |")
        a(f"| Relevé | {p['releve_le']} |")
        a("")
        if offres is not None:
            if offres == 0:
                a("**Personne n'a encore répondu.** C'est exactement la fenêtre visée : "
                  "arriver avec la page déjà en ligne avant le premier devis.")
            elif offres <= 3:
                a(f"**{offres} offre(s) déjà déposée(s).** La fenêtre est encore ouverte, "
                  "mais elle se referme. Ce sont des devis, pas des maquettes.")
            else:
                a(f"**{offres} offres déjà déposées.** Tard pour un devis de plus. "
                  "Ne vaut le coup que si la maquette peut sortir dans l'heure.")
            a("")
        if p["brief"]:
            a("**Le brief, tel qu'il est publié :**")
            a("")
            a("> " + p["brief"])
            a("")

    if mesure:
        a("## Son site aujourd'hui, mesuré")
        a("")
        a("| | |")
        a("|---|---|")
        a(f"| Adresse | {mesure.get('url', '')} |")
        a(f"| HTTPS | {'oui' if mesure.get('https') else '**non**'} |")
        a(f"| Poids du HTML | {mesure.get('poids_html_ko', '?')} Ko |")
        if mesure.get("images_mesurees"):
            a(f"| Images pesées | {mesure['images_mesurees']} pour "
              f"{mesure.get('poids_images_ko', 0)} Ko |")
        a(f"| Balise viewport | {'oui' if mesure.get('viewport') else '**absente**'} |")
        a(f"| Titre H1 | {'oui' if mesure.get('h1') else '**absent**'} |")
        a(f"| Scripts externes | {mesure.get('nb_scripts', '?')} |")
        if mesure.get("generator"):
            a(f"| Fabriqué avec | {mesure['generator']} |")
        if mesure.get("titre"):
            a(f"| title | {mesure['titre'][:90]} |")
        a("")
        constat = probe.constat(mesure) if probe else None
        if constat:
            a(f"**Constat utilisable tel quel :** {constat}")
            a("")

    if ident and ident.get("chantier"):
        a("## Sa marque : rien à relever, et c'est le sujet")
        a("")
        a(f"`{ident['url']}` sert une **{ident['chantier']}**. Tout ce qu'on y "
          "trouverait (logo, couleurs, images) appartient à l'hébergeur, pas à lui. "
          "Rien n'a donc été récupéré : le présenter comme sa marque serait inventer.")
        a("")
        a("**Ce que ça change pour la maquette.** L'identité est à construire, pas à "
          "reprendre. Cherche son logo ailleurs : réseaux sociaux, plaquette PDF, "
          "photo de camion ou de devanture, annuaire professionnel. Si rien n'existe, "
          "la page porte un logotype dessiné et on le dit dans la page.")
        a("")
    elif ident:
        a("## Sa marque, relevée sur son site")
        a("")
        if ident["palette"]:
            a("**Couleurs**, par fréquence dans son CSS. Les gris et les blancs sont écartés.")
            a("")
            for c in ident["palette"]:
                a(f"- `{c['couleur']}` ({c['occurrences']} fois)")
            a("")
        else:
            a("**Aucune couleur de marque détectée.** Site en gris et blanc, "
              "ou couleurs posées en image. À relever à l'œil.")
            a("")
        if ident["polices"]:
            a("**Polices déclarées :** " + ", ".join(
                f"{p['police']}" for p in ident["polices"]))
            a("")
        if ident.get("medias"):
            a(f"**{len(ident['medias'])} fichiers récupérés** dans `medias/`, "
              "logo compris quand il a été trouvé. Ce sont ses vraies images : "
              "elles servent de base, et tout ce qui n'est pas de lui doit porter "
              "la mention « photo d'illustration ».")
            a("")
            for m in ident["medias"][:12]:
                a(f"- `{os.path.basename(m['fichier'])}` "
                  f"({m['octets'] // 1024} Ko) — {m['url'][:80]}")
            a("")

    if directions:
        # La direction se déduit du métier, pas de mon humeur du jour. C'est ce
        # qui empêche la cinquième maquette de ressembler aux quatre premières.
        source = " ".join(filter(None, [
            nom,
            (p or {}).get("titre", ""),
            (p or {}).get("brief", ""),
            (ident or {}).get("titre_page", ""),
            (mesure or {}).get("titre", ""),
        ]))
        a(directions.bloc_markdown(source))

    if dispositifs:
        # Une direction ne suffit pas : deux pages peuvent avoir des palettes
        # opposées et le même squelette. C'est arrivé le 31/08/2026 avec
        # MECA 02 et Padel Presqu'île. L'interdit porte donc sur la structure.
        a(dispositifs.bloc_markdown())

    a("## Avant d'écrire une ligne de la page")
    a("")
    a("- [ ] Une seule page, pas trois directions. Un artisan qui offre son travail "
      "fabrique une chose, pas un catalogue.")
    a("- [ ] Un vrai morceau technique dedans, tiré de SON métier, que personne "
      "ne peut copier-coller d'un thème.")
    a("- [ ] Couleurs et polices tirées de sa marque, pas de la mienne.")
    a("- [ ] Chaque chiffre affiché vient d'une source citée dans ce dossier.")
    a("- [ ] Ce qui n'est pas de lui est marqué comme tel, en toutes lettres, "
      "dans la page.")
    a("- [ ] Le nom du projet Vercel ne contient pas « speerla ».")
    a("")
    return "\n".join(L)


def socle_html(nom, ident, mesure, p):
    """Le point de depart d'une maquette : ses couleurs, ses polices, ses faits.

    Volontairement SANS mise en page. Pas de hero, pas de grille, pas de
    sections toutes faites : un gabarit recolore se voit au premier coup d'oeil
    et c'est exactement ce qu'on refuse. Ce fichier ne fait gagner que le temps
    qui ne merite pas d'etre passe : declarer les bonnes couleurs, charger les
    bonnes polices, et avoir sous la main les chiffres qu'on a le droit de citer.
    """
    couleurs = [c["couleur"] for c in (ident or {}).get("palette", [])][:5]
    tokens = "\n".join("      --marque-%d: %s;" % (i + 1, c)
                        for i, c in enumerate(couleurs)) or \
        "      /* aucune couleur relevee : a prendre sur son logo ou ses photos */"

    familles = [f["police"] for f in (ident or {}).get("polices", [])][:2]
    lien_polices = ""
    if familles:
        q = "&".join("family=" + f.replace(" ", "+") + ":wght@400;600;800"
                     for f in familles)
        lien_polices = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
                        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                        '<link href="https://fonts.googleapis.com/css2?%s&display=swap" '
                        'rel="stylesheet">' % q)
    pile = ", ".join('"%s"' % f for f in familles) or "system-ui"

    faits = []
    if mesure:
        if not mesure.get("https"):
            faits.append("pas de HTTPS sur le site actuel")
        if mesure.get("poids_images_ko", 0) > 1500:
            faits.append("page d'accueil a %.1f Mo d'images"
                         % ((mesure.get("poids_images_ko", 0) + mesure.get("poids_html_ko", 0)) / 1024))
        if not mesure.get("h1"):
            faits.append("aucun titre H1")
        if not mesure.get("viewport"):
            faits.append("aucune balise viewport")
        if mesure.get("nb_scripts", 0) >= 20:
            faits.append("%d scripts externes" % mesure["nb_scripts"])
        if mesure.get("generator"):
            faits.append("fait avec %s" % mesure["generator"])
    liste_faits = "\n".join("    <li>%s</li>" % f for f in faits) or \
        "    <li>rien de mesure pour l'instant</li>"

    medias = [m["fichier"].split("/")[-1].split("\\")[-1]
              for m in (ident or {}).get("medias", [])][:10]
    liste_medias = "\n".join("    <li>medias/%s</li>" % m for m in medias) or \
        "    <li>aucun media recupere</li>"

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>%(nom)s</title>
%(polices)s
<style>
  :root {
%(tokens)s
    --texte: #14161a;
    --fond: #ffffff;
  }
  /* Les polices du client, chargees. La mise en page reste a dessiner :
     ce fichier ne contient volontairement aucune grille ni aucun bloc tout
     fait, pour qu'aucune maquette ne ressemble a la precedente. */
  body { margin:0; background:var(--fond); color:var(--texte);
         font-family:%(pile)s, system-ui, sans-serif; }
  .chantier { max-width:44rem; margin:8vh auto; padding:0 1.5rem;
              font:400 15px/1.6 ui-monospace, monospace; }
  .chantier h1 { font-size:1.4rem; }
  .chantier ul { padding-left:1.2rem; }
  .puces { display:flex; gap:.5rem; margin:1rem 0; }
  .puce { width:44px; height:44px; border-radius:6px; border:1px solid #0002; }
</style>

<div class="chantier">
  <h1>%(nom)s</h1>
  <p><strong>Socle, pas maquette.</strong> Ce fichier porte ses couleurs, ses
  polices et ses faits. La page se dessine a partir d'ici, de zero.</p>

  <div class="puces">%(puces)s</div>

  <h2>Ce qui est mesure, donc citable</h2>
  <ul>
%(faits)s
  </ul>

  <h2>Ses fichiers, deja telecharges</h2>
  <ul>
%(medias)s
  </ul>

  <h2>Avant de livrer</h2>
  <ul>
    <li>ce qui n'est pas de lui porte la mention "illustration", en clair</li>
    <li>aucun chiffre affiche qui ne soit pas dans DOSSIER.md</li>
    <li>aucun temoignage, aucun logo client invente</li>
    <li>recette en 390 px avant de deployer</li>
  </ul>
</div>
""" % {"nom": H.escape(nom), "polices": lien_polices, "tokens": tokens,
       "pile": pile, "faits": liste_faits, "medias": liste_medias,
       "puces": "".join('<span class="puce" style="background:%s"></span>' % c
                        for c in couleurs)}


def main():
    ap = argparse.ArgumentParser(description="Kit de départ d'une maquette Codeur.")
    ap.add_argument("projet", nargs="?", help="id ou URL du projet Codeur")
    ap.add_argument("--site", help="domaine du client, si le brief ne le donne pas")
    ap.add_argument("--nom", help="nom du client ou du projet, pour le dossier")
    ap.add_argument("--page", action="store_true",
                    help="ecrit aussi index.html, le socle de la maquette")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not args.projet and not args.site:
        ap.error("donne un projet Codeur, ou --site")

    p = projet(args.projet) if args.projet else None

    domaine = args.site
    if not domaine and p and probe:
        domaine = probe.trouver_domaine(p["titre"], p["brief"])
    if domaine:
        print(f"  site du client : {domaine}")

    mesure = probe.mesurer(domaine) if (domaine and probe) else None
    ident = identite(domaine) if domaine else None

    nom = args.nom or (p["titre"] if p else domaine)
    slug = re.sub(r"[^a-z0-9]+", "-", (nom or "kit").lower()).strip("-")[:50]
    if p and p["id"]:
        slug = f"{p['id']}-{slug}"
    sortie = os.path.join(KITS, slug)
    os.makedirs(sortie, exist_ok=True)

    if ident:
        ident["medias"] = telecharge(
            ([ident["logo"]] if ident["logo"] else []) + ident["images"][:8],
            os.path.join(sortie, "medias"))
        with open(os.path.join(sortie, "identite.json"), "w", encoding="utf-8") as f:
            json.dump(ident, f, ensure_ascii=False, indent=2)

    if args.page:
        with open(os.path.join(sortie, "index.html"), "w", encoding="utf-8") as f:
            f.write(socle_html(nom, ident, mesure, p))
        print("  socle ecrit : index.html")

    md = dossier_md(p, mesure, ident, nom)
    with open(os.path.join(sortie, "DOSSIER.md"), "w", encoding="utf-8") as f:
        f.write(md)

    print()
    print(md)
    print(f"\n  -> {os.path.relpath(sortie, HERE)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
