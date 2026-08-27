# -*- coding: utf-8 -*-
"""
Radar BODACC : les entreprises qui viennent de se créer, filtrées sur les
activités qui ont besoin d'un site.

Source : BODACC open data, sans clé.
Tourne dans le cloud parce que les hôtes data.gouv et opendatasoft sont
injoignables depuis la connexion de travail actuelle (constaté le 27/08/2026).

Usage :
    python radar.py                      # départements par défaut
    python radar.py 44 85 35             # départements choisis
    python radar.py --notify             # + email du digest
    python radar.py --all                # ignore l'état, ressort tout
"""

import argparse
import csv
import html as H
import json
import os
import sys
import unicodedata
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "radar-state.json")
CSV_OUT = os.path.join(HERE, "radar-creations.csv")
DATASET = "annonces-commerciales"
BASE = ("https://bodacc-datadila.opendatasoft.com/api/explore/v2.1"
        "/catalog/datasets/%s/records" % DATASET)
PAGES = 5
PER = 100

# Littoral et villes touristiques aisées, là où un commerce peut payer un vrai site.
DEPTS_DEFAUT = ["44", "85", "35", "56", "29", "17", "33", "64", "06", "83"]

# Activités qui ont besoin d'un site et de visibilité.
RELEVANT = [
    "restaur", "brasserie", "traiteur", "boulang", "patiss", "cafe", "creperie", "crep",
    "pizz", "food", "salon de the", "glacier", "bar a ",
    "hotel", "chambre d", "gite", "hebergement", "camping", "maison d hotes",
    "coiffure", "coiffeur", "barbier", "esthet", "ongulaire", "beaute", "spa", "massage",
    "institut", "onglerie", "maquillage", "bien-etre", "bien etre",
    "deco", "decorat", "design d espace", "architect", "paysag", "jardin", "fleur",
    "menuis", "ebenist", "plomb", "electric", "macon", "peinture", "carrel", "couvreur",
    "bricolage", "homme toutes mains", "renovation", "artisan", "amenagement", "terrass",
    "boutique", "vente de", "achat-vente", "achat et vente", "pret-a-porter", "vetement",
    "bijou", "maroquinerie", "chaussure", "concept store", "epicerie", "primeur",
    "boucher", "fromager", "caviste", "poissonn", "chocolat",
    "photograph", "video", "graphis", "tatouage", "tattoo",
    "fitness", "coach", "yoga", "pilates", "naturopath", "osteopath", "sophrolog",
    "kine", "therap", "praticien", "reflexolog", "psycho",
    "garage", "carrosserie", "lavage", "auto-ecole", "auto ecole",
    "fleuriste", "toilettage", "animaler", "ferme",
]

# Financier, immobilier d'investissement, pur juridique : à jeter.
EXCLUDE = [
    "holding", "participation", "prise de tous interet", "prise d interet",
    "gestion de biens", "gestion a titre civil", "gestion d un patrimoine",
    "marchand de biens", "location de biens", "mise en location", "location immobil",
    "acquisition, la detention", "detention, la propriete", "civile immobil",
    "fonciere", "portefeuille", "valeurs mobil", "societe civile immob",
    "achat et mise en location", "acquisition par voie d achat ou d apport",
]


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("'", " ")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "speerla-radar/1.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def jload(v):
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {}
    return {}


def activite_of(rec):
    acte = jload(rec.get("acte"))
    act = (acte.get("creation") or {}).get("activite") or ""
    if not act:
        et = jload(rec.get("listeetablissements")).get("etablissement") or {}
        if isinstance(et, list):
            et = et[0] if et else {}
        act = et.get("activite") or ""
    return act


def is_target(activite, nom):
    na, nn = norm(activite), norm(nom)
    if nn.startswith("sci ") or " sci " in " %s " % nn:
        return False
    if any(x in na for x in EXCLUDE):
        return False
    return any(x in na for x in RELEVANT)


def fetch_dept(dept):
    rows = []
    where = 'familleavis="creation" and numerodepartement="%s"' % dept
    for p in range(PAGES):
        url = ("%s?where=%s&order_by=dateparution%%20desc&limit=%d&offset=%d"
               % (BASE, urllib.parse.quote(where), PER, p * PER))
        try:
            d = get(url)
        except Exception as e:
            print("  [dept %s] page %d : %s" % (dept, p, e), file=sys.stderr)
            break
        res = d.get("results", [])
        if not res:
            break
        for r in res:
            act = activite_of(r)
            nom = r.get("commercant") or ""
            if not is_target(act, nom):
                continue
            acte = jload(r.get("acte"))
            rows.append({
                "id": str(r.get("id") or "%s|%s" % (norm(nom), norm(r.get("ville") or ""))),
                "nom": nom,
                "ville": r.get("ville") or "",
                "cp": r.get("cp") or "",
                "dept": dept,
                "date": acte.get("dateCommencementActivite") or r.get("dateparution") or "",
                "activite": " ".join((act or "").split())[:200],
                "bodacc": r.get("url_complete") or "",
            })
    return rows


def charger_etat():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return set(json.load(f).get("vus", []))
    return set()


def sauver_etat(ids):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({"vus": sorted(ids)}, f)


def ecrire_csv(rows):
    champs = ["nom", "ville", "cp", "dept", "date", "activite", "bodacc"]
    with open(CSV_OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def email_html(rows):
    lignes = []
    for r in rows:
        lien = ('<a href="%s" style="color:#0f172a">l\'annonce</a>' % H.escape(r["bodacc"])
                if r["bodacc"] else "")
        lignes.append(
            '<tr>'
            '<td style="padding:9px 10px;border-bottom:1px solid #eceff3;font:400 12px monospace;color:#6b7280;white-space:nowrap">%s</td>'
            '<td style="padding:9px 10px;border-bottom:1px solid #eceff3;font:600 13px -apple-system,Segoe UI,sans-serif;color:#0f172a">%s'
            '<div style="font:400 12px -apple-system,Segoe UI,sans-serif;color:#6b7280">%s %s</div></td>'
            '<td style="padding:9px 10px;border-bottom:1px solid #eceff3;font:400 12px -apple-system,Segoe UI,sans-serif;color:#374151">%s</td>'
            '<td style="padding:9px 10px;border-bottom:1px solid #eceff3;font:400 12px -apple-system,Segoe UI,sans-serif;white-space:nowrap">%s</td>'
            '</tr>' % (H.escape(r["date"][:10]), H.escape(r["nom"][:52]),
                       H.escape(r["cp"]), H.escape(r["ville"][:24]),
                       H.escape(r["activite"][:130]), lien))
    return """<div style="max-width:820px;margin:0 auto;padding:26px 18px;background:#fff">
  <div style="font:700 15px -apple-system,Segoe UI,sans-serif;color:#0f172a;margin:0 0 4px">Radar BODACC</div>
  <div style="font:400 13px -apple-system,Segoe UI,sans-serif;color:#6b7280;margin:0 0 20px">
    {n} entreprise(s) qui viennent de se créer et qui auront besoin d'un site.
    Ni email ni site dans la source : l'étape suivante est l'enrichissement.</div>
  <table style="width:100%;border-collapse:collapse">{lignes}</table>
  <div style="font:400 12px -apple-system,Segoe UI,sans-serif;color:#9ca3af;border-top:1px solid #eceff3;padding-top:14px;margin-top:16px">
    Le CSV complet est en pièce jointe de la passe GitHub (onglet Artifacts).</div>
</div>""".format(n=len(rows), lignes="".join(lignes))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("depts", nargs="*", help="numéros de départements")
    p.add_argument("--notify", action="store_true")
    p.add_argument("--all", action="store_true", help="ignore l'état déjà vu")
    p.add_argument("--max", type=int, default=60, help="nb max de lignes dans l'email")
    args = p.parse_args()

    depts = [d.zfill(2) for d in (args.depts or DEPTS_DEFAUT)]
    etat = set() if args.all else charger_etat()

    toutes = []
    for d in depts:
        print("Radar BODACC dept %s" % d)
        toutes += fetch_dept(d)

    # dédoublonnage interne puis contre l'état
    vues, uniques = set(), []
    for r in toutes:
        cle = (norm(r["nom"]), norm(r["ville"]))
        if cle in vues:
            continue
        vues.add(cle)
        uniques.append(r)

    neuves = [r for r in uniques if r["id"] not in etat]
    for r in uniques:
        etat.add(r["id"])
    sauver_etat(etat)
    ecrire_csv(neuves)

    print("\n%d création(s) pertinentes, dont %d nouvelles depuis la dernière passe."
          % (len(uniques), len(neuves)))
    for r in neuves[:30]:
        print("  %s | %s %-18s | %-30s | %s"
              % (r["date"][:10], r["cp"], r["ville"][:18], r["nom"][:30], r["activite"][:60]))

    if args.notify and neuves:
        import notify
        try:
            res = notify.envoyer_html(
                "Radar BODACC : %d nouvelles entreprises" % len(neuves),
                email_html(neuves[:args.max]))
            print("\nemail envoye (%s)" % res.get("id", "?"))
        except Exception as e:
            print("\nemail KO : %s" % e, file=sys.stderr)
    elif args.notify:
        print("\nrien de neuf, pas d'email")


if __name__ == "__main__":
    main()
