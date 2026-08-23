# -*- coding: utf-8 -*-
"""
Veille Codeur.com : detecte les nouveaux projets qui matchent Speerla,
les score, et sort un digest pret a repondre.

Source : https://www.codeur.com/projects.rss (public, sans compte).
Le flux accepte ?q=<recherche>.

Usage :
    python watch.py                    # 1 passe, uniquement les nouveautes
    python watch.py --loop 90          # boucle toutes les 90 s
    python watch.py --all              # ignore l'etat, rejoue tout le flux
    python watch.py --min-score 8      # seuil de pertinence (defaut 6)
    python watch.py --min-budget 1000  # plancher budget (defaut 500)
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
FEED = "https://www.codeur.com/projects.rss"
UA = "Mozilla/5.0 (compatible; SpeerlaWatch/1.0; +https://speerlastudio.com)"

QUERIES = ["", "site internet", "refonte site", "site vitrine", "wordpress", "landing page"]

POSITIF = {
    5: ["refonte", "refaire mon site", "site obsolete", "moderniser le site", "migration"],
    4: ["site vitrine", "site internet", "site web", "landing page", "creation de site",
        "nextjs", "next.js", "site e-commerce", "boutique en ligne", "site cle en main"],
    3: ["wordpress", "webflow", "shopify", "wix", "one page", "site institutionnel",
        "restaurant", "hotel", "artisan", "cabinet", "immobilier", "react"],
    2: ["seo", "performance", "responsive", "maquette", "figma", "web design",
        "experience utilisateur"],
}
NEGATIF = ["community manager", "community management", "redaction d'articles", "redacteur web",
           "montage video", "jeu video", "pixel art", "unity", "crypto", "trading",
           "saisie de donnees", "data entry", "traduction de documents", "prospection commerciale",
           "call center", "standard telephonique", "comptabilite", "juridique"]

BUDGET_PALIERS = [("10 000", 10000), ("5 000", 5000), ("1 000", 1000), ("500", 500)]


def norm(s):
    s = html.unescape(s or "").lower()
    return s.translate(str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc"))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def parse_budget(desc):
    m = re.search(r"Budget\s*:\s*(.+?)\s*-\s*Cat", desc)
    label = html.unescape(m.group(1).strip()) if m else "?"
    flat = norm(label).replace("\u202f", "").replace("\xa0", "").replace(" ", "")
    if "moinsde500" in flat:
        return label, 0
    for token, val in BUDGET_PALIERS:
        if token.replace(" ", "") in flat:
            return label, val
    return label, 0


def parse_categories(desc):
    m = re.search(r"Cat[eé]gories\s*:\s*(.+?)</p>", desc)
    return html.unescape(m.group(1).strip()) if m else ""


def clean_text(desc):
    txt = re.sub(r"<p>\s*Budget\s*:.*?</p>", " ", desc, count=1, flags=re.S)
    txt = re.sub(r"<a\b[^>]*>.*?</a>", " ", txt, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html.unescape(html.unescape(txt))
    return re.sub(r"\s+", " ", txt).strip()


def score(item):
    hay = norm(item["title"] + " " + item["body"] + " " + item["cats"])
    pts, hits = 0, []
    for weight, words in POSITIF.items():
        for w in words:
            if norm(w) in hay:
                pts += weight
                hits.append(w)
                break
    for w in NEGATIF:
        if norm(w) in hay:
            pts -= 4
            hits.append("!" + w)
    if item["budget_min"] >= 5000:
        pts += 3
    elif item["budget_min"] >= 1000:
        pts += 2
    elif item["budget_min"] == 0:
        pts -= 3
    return pts, hits


def collect():
    seen, out = set(), []
    for q in QUERIES:
        url = FEED + ("?q=" + urllib.parse.quote(q) if q else "")
        try:
            root = ET.fromstring(fetch(url))
        except Exception as e:
            print("  (flux KO %s : %s)" % (q or "tous", e), file=sys.stderr)
            continue
        for it in root.iter("item"):
            gid = (it.findtext("guid") or "").strip()
            if not gid or gid in seen:
                continue
            seen.add(gid)
            desc = it.findtext("description") or ""
            label, bmin = parse_budget(desc)
            try:
                pub = parsedate_to_datetime(it.findtext("pubDate"))
            except Exception:
                pub = datetime.now(timezone.utc)
            item = {
                "id": gid,
                "title": html.unescape(it.findtext("title") or ""),
                "url": (it.findtext("link") or "").strip(),
                "pub": pub,
                "budget": label,
                "budget_min": bmin,
                "cats": parse_categories(desc),
                "body": clean_text(desc),
            }
            item["score"], item["hits"] = score(item)
            out.append(item)
    return sorted(out, key=lambda i: i["pub"], reverse=True)


def load_state():
    if os.path.exists(STATE):
        with open(STATE, "r", encoding="utf-8") as f:
            return set(json.load(f).get("seen", []))
    return set()


def save_state(ids):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({"seen": sorted(ids), "updated": datetime.now().isoformat()}, f)


def render(item):
    mins = int((datetime.now(timezone.utc) - item["pub"]).total_seconds() // 60)
    age = "%d min" % mins if mins < 120 else "%d h" % (mins // 60)
    body = item["body"][:350] + ("..." if len(item["body"]) > 350 else "")
    return ("\n[%d pts] %s\n"
            "  il y a %s | budget : %s\n"
            "  %s\n"
            "  cat. : %s\n"
            "  > %s\n" % (item["score"], item["title"], age, item["budget"],
                          item["url"], item["cats"], body))


def age_h(item):
    return (datetime.now(timezone.utc) - item["pub"]).total_seconds() / 3600


def run_once(args, state):
    items = collect()
    fresh = [i for i in items
             if (args.all or i["id"] not in state)
             and i["score"] >= args.min_score
             and i["budget_min"] >= args.min_budget
             and (not args.max_age or age_h(i) <= args.max_age)]
    for i in items:
        state.add(i["id"])
    save_state(state)
    stamp = datetime.now().strftime("%H:%M:%S")
    if not fresh:
        print("%s  rien de neuf (%d projets scannes)" % (stamp, len(items)))
        return
    print("%s  %d projet(s) pour Speerla sur %d scannes" % (stamp, len(fresh), len(items)))
    fresh = sorted(fresh, key=lambda x: (-x["score"], x["pub"]))
    for i in fresh:
        print(render(i))
    if args.notify:
        import draft
        import notify
        import probe
        brouillons = {}
        for i in fresh:
            mins = int(age_h(i) * 60)
            i["age"] = "%d min" % mins if mins < 120 else "%d h" % (mins // 60)
            # si le brief cite un site, on va le mesurer pour ouvrir sur un fait
            constat = None
            hote = probe.trouver_domaine(i["title"], i["body"])
            if hote:
                try:
                    constat = probe.constat(probe.mesurer(hote))
                    print("  site mesure : %s" % hote)
                except Exception as e:
                    print("  mesure impossible (%s) : %s" % (hote, e), file=sys.stderr)
            brouillons[i["id"]] = draft.rediger(i["title"], i["body"], i["cats"],
                                                i["budget"], constat)
        try:
            res = notify.envoyer(fresh, brouillons)
            print("  email envoye (%s)" % res.get("id", "?"))
        except Exception as e:
            print("  email KO : %s" % e, file=sys.stderr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--loop", type=int, default=0, help="secondes entre 2 passes")
    p.add_argument("--all", action="store_true", help="ignore l'etat deja vu")
    p.add_argument("--min-score", type=int, default=6)
    p.add_argument("--min-budget", type=int, default=500,
                   help="plancher budget en euros (0 = tout garder)")
    p.add_argument("--notify", action="store_true",
                   help="envoie le digest par email (RESEND_API_KEY requis)")
    p.add_argument("--max-age", type=float, default=0,
                   help="ne garder que les projets publies il y a moins de N heures")
    args = p.parse_args()
    state = set() if args.all else load_state()
    while True:
        run_once(args, state)
        if not args.loop:
            break
        time.sleep(args.loop)


if __name__ == "__main__":
    main()
