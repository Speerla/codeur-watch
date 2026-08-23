# -*- coding: utf-8 -*-
"""
Génère un brouillon de réponse Codeur à partir du brief du projet.
Voix Speerla : direct, concret, zéro jargon, zéro tiret cadratin,
et surtout zéro fait inventé (aucune référence client, aucun chiffre sorti du chapeau).
"""

import re


def _norm(s):
    return (s or "").lower().translate(
        str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc"))


STACKS = [
    ("wordpress", "WordPress"), ("divi", "WordPress"), ("elementor", "WordPress"),
    ("shopify", "Shopify"), ("prestashop", "PrestaShop"), ("woocommerce", "WooCommerce"),
    ("wix", "Wix"), ("webflow", "Webflow"), ("squarespace", "Squarespace"),
    ("next", "Next.js"), ("react", "React"),
]

SECTEURS = [
    ("restaurant", "restaurant"), ("hotel", "hôtel"), ("chambre d'hote", "chambre d'hôtes"),
    ("immobilier", "immobilier"), ("agence de voyage", "voyage"), ("avocat", "cabinet"),
    ("cabinet", "cabinet"), ("artisan", "artisanat"), ("paysagiste", "paysagisme"),
    ("industri", "industrie"), ("cosmetique", "cosmétique"), ("association", "association"),
    ("btp", "BTP"), ("formation", "formation"), ("sport", "sport"),
]

BESOINS = [
    ("multilingue", "le multilingue"), ("trois langues", "le multilingue"),
    ("deux langues", "le multilingue"), ("anglais", "le multilingue"),
    ("reservation", "la réservation en ligne"), ("rendez-vous", "la prise de rendez-vous"),
    ("paiement", "le tunnel de paiement"), ("panier", "le tunnel de paiement"),
    ("seo", "la structure SEO"), ("referencement", "la structure SEO"),
    ("mobile", "le rendu mobile"), ("responsive", "le rendu mobile"),
    ("performance", "la vitesse de chargement"), ("temps de chargement", "la vitesse de chargement"),
    ("charte graphique", "la direction visuelle"), ("identite visuelle", "la direction visuelle"),
    ("web design", "la direction visuelle"),
    ("formulaire", "les formulaires"), ("blog", "la partie blog"),
    ("crm", "la connexion au CRM"), ("api", "les connexions API"),
    ("migration", "la reprise du contenu existant"),
    ("newsletter", "la collecte d'emails"),
]

URGENCE = ["urgent", "au plus vite", "des que possible", "avant le ", "deadline",
           "delai court", "delai serre", "dans les plus brefs"]

TOURNURES = [
    "Je commence par %s, parce que c'est ce qui fait dérailler ce genre de projet quand on le garde pour la fin.",
    "Sur %s, je vous montre le fonctionnement réel avant de l'intégrer, pas une capture d'écran.",
    "Je cadre %s noir sur blanc dans le devis, jamais en zone floue.",
]


def analyse(titre, brief, categories):
    hay = _norm(" ".join([titre or "", brief or "", categories or ""]))
    stack = next((label for k, label in STACKS if k in hay), None)
    secteur = next((label for k, label in SECTEURS if k in hay), None)
    besoins, vus = [], set()
    for k, label in BESOINS:
        if k in hay and label not in vus:
            vus.add(label)
            besoins.append(label)
    refonte = any(k in hay for k in ("refonte", "refaire", "moderniser", "migration", "obsolete", "vieillissant"))
    urgent = any(k in hay for k in URGENCE)
    return {"stack": stack, "secteur": secteur, "besoins": besoins[:3],
            "refonte": refonte, "urgent": urgent}


def phrase_cle(brief):
    """Reprend une phrase du brief pour prouver qu'on l'a lu."""
    brief = re.sub(r"\s+", " ", brief or "").strip()
    for p in re.split(r"(?<=[.;:])\s+", brief):
        p = p.strip(" .;:…")
        if 40 <= len(p) <= 170 and not _norm(p).startswith(("bonjour", "cahier des charges")):
            return p
    return brief[:150].strip(" .…")


def rediger(titre, brief, categories="", budget="", constat=None):
    """constat : phrase issue d'une mesure réelle du site du client (probe.py), ou None."""
    a = analyse(titre, brief, categories)
    cite = phrase_cle(brief)

    # un constat mesuré prouve qu'un site tourne déjà : ce n'est jamais une page blanche
    if constat:
        a["refonte"] = True
    if a["refonte"]:
        ouverture = ("Vous ne partez pas de zéro, vous remplacez quelque chose qui tourne déjà. "
                     "C'est plus délicat qu'une création, parce qu'il faut moderniser sans casser "
                     "ce qui vous ramène des clients aujourd'hui.")
    else:
        ouverture = ("Vous partez d'une page blanche, donc tout se joue sur les décisions des deux "
                     "premières semaines. C'est là que se décide si le site vous sert vraiment "
                     "ou s'il reste une carte de visite.")

    # Un constat mesuré vaut mieux que n'importe quelle accroche : il prouve
    # qu'on a ouvert le site avant d'écrire. Il passe donc en premier.
    accroche = "Bonjour,\n\n"
    if constat:
        accroche += constat + " " + ouverture
    else:
        accroche += ouverture
    if cite:
        accroche += "\n\nCe que je retiens de votre brief : %s." % cite.rstrip(".")

    lignes = []
    if a["stack"]:
        lignes.append("Je peux rester sur %s si c'est le bon outil pour vous. Si ce n'est pas le cas, "
                      "je vous le dis avant de commencer, pas au milieu du projet." % a["stack"])
    for i, b in enumerate(a["besoins"]):
        lignes.append(TOURNURES[i % len(TOURNURES)] % b)
    if not lignes:
        lignes.append("Je commence par cadrer ce que le site doit vous rapporter concrètement, "
                      "avant de parler de design.")

    methode = ("Ma façon de travailler : je vous montre une maquette de la page principale avant de "
               "coder quoi que ce soit. Vous voyez le résultat, vous tranchez, on avance seulement après.")

    positionnement = ("Je suis indépendant, pas une agence. Vous parlez directement à la personne qui "
                      "fait le travail, et le budget ne se dilue pas dans des couches intermédiaires.")

    if a["urgent"]:
        cloture = ("Vous mentionnez un délai serré : donnez-moi votre date butoir, je vous dis "
                   "franchement si elle est tenable avant qu'on aille plus loin.")
    else:
        cloture = ("Si ça vous parle, dites-moi simplement quelle page compte le plus pour vous. "
                   "Je vous envoie une première proposition visuelle dessus.")

    corps = "\n\n".join([
        accroche,
        "\n".join("- " + l for l in lignes[:3]),
        methode,
        positionnement,
        cloture,
        "Cordialement,\nRobin Bouvet\nSpeerla Studio\nspeerlastudio.com",
    ])
    # règle maison : jamais de tiret cadratin
    return corps.replace("\u2014", ",").replace("\u2013", ",")
