# -*- coding: utf-8 -*-
"""
Quand un brief mentionne un site existant, on va le mesurer pour de vrai.
Objectif : mettre un constat chiffré dans la réponse, pas une formule creuse.
On ne renvoie que ce qu'on a réellement mesuré.
"""

import re
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# domaines à ignorer : plateformes, réseaux, exemples
IGNORE = {"codeur.com", "www.codeur.com", "gmail.com", "google.com", "facebook.com",
          "instagram.com", "linkedin.com", "youtube.com", "wordpress.org", "shopify.com",
          "wix.com", "example.com", "site.com", "monsite.fr"}

DOMAINE = re.compile(
    r"\b((?:https?://)?(?:www\.)?[a-z0-9][a-z0-9\-]{1,61}\.(?:fr|com|net|org|eu|be|ch|io|co|shop|store|paris))\b",
    re.I)


def trouver_domaine(*textes):
    for t in textes:
        for brut in DOMAINE.findall(t or ""):
            hote = brut.lower().replace("https://", "").replace("http://", "").strip("/")
            if hote.startswith("www."):
                hote = hote[4:]
            if hote in IGNORE or hote.replace("www.", "") in IGNORE:
                continue
            if hote.split(".")[0] in ("mail", "contact", "info", "cabinet"):
                continue
            return hote
    return None


def _get(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "text/html,*/*"})
    ctx = ssl.create_default_context()
    debut = time.time()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        corps = r.read(4_000_000)
        return {"url": r.geturl(), "code": r.status, "html": corps,
                "ms": int((time.time() - debut) * 1000)}


def mesurer(hote):
    """Renvoie un dict de faits mesurés, ou None si le site ne répond pas."""
    for schema in ("https://", "http://"):
        try:
            r = _get(schema + hote)
            break
        except (urllib.error.URLError, socket.timeout, ssl.SSLError, OSError):
            r = None
    if not r:
        return None

    html = r["html"].decode("utf-8", errors="replace")
    poids_html = len(r["html"])
    images = re.findall(r"<img\b[^>]*", html, re.I)
    scripts = re.findall(r"<script\b[^>]*src=", html, re.I)
    styles = re.findall(r"<link\b[^>]*rel=[\"']?stylesheet", html, re.I)

    # poids réel des ressources principales de la page d'accueil
    srcs = re.findall(r"<img\b[^>]*src=[\"']([^\"']+)", html, re.I)[:12]
    poids_images, mesurees = 0, 0
    for s in srcs:
        if s.startswith("data:"):
            continue
        abs_url = urllib.parse.urljoin(r["url"], s)
        try:
            req = urllib.request.Request(abs_url, method="HEAD",
                                         headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=6) as rr:
                taille = int(rr.headers.get("Content-Length") or 0)
                if taille:
                    poids_images += taille
                    mesurees += 1
        except Exception:
            continue

    return {
        "hote": hote,
        "url": r["url"],
        "https": r["url"].startswith("https://"),
        "ms": r["ms"],
        "poids_html_ko": round(poids_html / 1024),
        "nb_images": len(images),
        "nb_scripts": len(scripts),
        "nb_styles": len(styles),
        "images_mesurees": mesurees,
        "poids_images_ko": round(poids_images / 1024),
        "viewport": bool(re.search(r"<meta[^>]*name=[\"']?viewport", html, re.I)),
        "titre": (re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S).group(1).strip()
                  if re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S) else ""),
        "h1": bool(re.search(r"<h1\b", html, re.I)),
        "generator": (re.search(r'<meta[^>]*name=["\']generator["\'][^>]*content=["\']([^"\']+)',
                                html, re.I).group(1)
                      if re.search(r'<meta[^>]*name=["\']generator["\']', html, re.I) else ""),
    }


def constat(m):
    """Une phrase, uniquement à partir de ce qui a été mesuré."""
    if not m:
        return None
    faits = []
    total_ko = m["poids_html_ko"] + m["poids_images_ko"]
    if m["images_mesurees"] >= 3 and total_ko > 2000:
        faits.append("la page d'accueil pèse déjà %.1f Mo sur les seules images que j'ai pu mesurer"
                     % (total_ko / 1024))
    elif m["poids_html_ko"] > 300:
        faits.append("le HTML seul de la page d'accueil fait %d Ko avant la moindre image"
                     % m["poids_html_ko"])
    if not m["viewport"]:
        faits.append("la page n'a pas de balise viewport, donc le mobile est laissé au hasard")
    if not m["https"]:
        faits.append("le site répond encore en HTTP simple")
    if not m["h1"]:
        faits.append("il n'y a aucun titre H1 sur la page d'accueil")
    if m["nb_scripts"] >= 20:
        faits.append("%d scripts externes sont chargés sur la page d'accueil" % m["nb_scripts"])
    if not faits:
        return None
    return "J'ai regardé %s avant de vous écrire : %s." % (m["hote"], faits[0])


if __name__ == "__main__":
    import sys
    hote = trouver_domaine(" ".join(sys.argv[1:])) or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not hote:
        print("aucun domaine trouvé")
        raise SystemExit(1)
    m = mesurer(hote)
    print(m)
    print("\nconstat :", constat(m))
