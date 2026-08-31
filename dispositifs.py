# -*- coding: utf-8 -*-
"""dispositifs.py — le journal de ce qui a déjà été utilisé, et l'interdit qui suit.

## Pourquoi ce fichier existe

Le 31 août 2026, deux maquettes livrées le même jour, MECA 02 et Padel Presqu'île,
avaient des palettes et des typographies entièrement différentes. Et pourtant elles
se ressemblaient, parce que **quatre sections portaient exactement le même chapeau
et le même titre** :

    [Ce que ça change]   [Si ça vous parle → Ce qui se passe ensuite]   [Transparence]

Changer les couleurs ne suffit pas. Ce qui se répète, ce n'est pas la peau, c'est
**l'architecture** : même en-tête collant à écusson, même chapeau souligné, même
« pièce technique » en position deux, mêmes cartes numérotées 01/02/03, même faux
résultat Google, même bloc vrai/inventé en deux colonnes.

## Les deux règles

**1. La page EST l'objet du métier, pas un site qui en parle.**
Un club de padel, sa page est un écran de réservation. Un atelier d'usinage, sa page
est un plan. Un caviste, sa page est une étagère. Un menuisier, sa page est un plan
de coupe. On ne fait pas « un site avec une section réservation », on fait la
réservation, et le reste s'organise autour.

**2. Un dispositif déjà utilisé est interdit sur les trois maquettes suivantes.**
Pas « à éviter ». Interdit. Sans quoi il revient toujours.

    python dispositifs.py                    # l'état du journal
    python dispositifs.py padel-presquile    # ce qui est interdit pour la suivante
"""

import sys
import unicodedata


def _norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# --------------------------------------------------------------------------- #
# Le catalogue des dispositifs, avec leur nom court
# --------------------------------------------------------------------------- #

CATALOGUE = {
    "entete-ecusson": "En-tête collant avec écusson dessiné à gauche, nav au centre, "
                      "bouton à droite",
    "chapeau-trait": "Petit chapeau en capitales espacées, précédé ou suivi d'un trait "
                     "de couleur",
    "titre-condense": "Titre géant en capitales, typographie condensée, deux couleurs "
                      "dans la même phrase",
    "cartouche-chiffres": "Bande de trois ou quatre chiffres clés en haut de page, "
                          "façon cartouche",
    "piece-technique-2": "La pièce technique animée placée en deuxième section",
    "cartes-numerotees": "Grille de trois ou quatre cartes avec 01 / 02 / 03 en petit "
                         "au-dessus du titre",
    "faux-google": "Aperçu d'un faux résultat de recherche Google dans un cadre",
    "suite-numerotee": "Liste numérotée « Ce qui se passe ensuite », trois ou quatre "
                       "étapes en colonnes",
    "vrai-invente": "Bloc final en deux colonnes, vérifié d'un côté, inventé de l'autre",
    "photos-etiquetees": "Galerie de photos en niveaux de gris avec la mention "
                         "« photo d'illustration »",
    "citation-filet": "Citation du client dans un filet vertical coloré",
    "compteur-avance": "Barre de progression ou compteur de pourcentage lié au "
                       "défilement",
    "bandeau-billet": "Bandeau supérieur en format billet : nom, ville, horloge, "
                      "état, sans logo ni menu",
    "rail-jours": "Rail vertical de sélection des jours à gauche, avec un grand "
                  "compteur en bas",
    "ticket-glissant": "Ticket blanc qui monte du bas de l'écran à la sélection",
    "verso-recu": "Le contenu secondaire imprimé à la suite comme le verso d'un "
                  "reçu, lignes libellé/valeur",
    "notes-lettres": "Notes d'honnêteté appelées par des lettres A, B, C collées "
                     "aux éléments concernés",
    "tete-numerotee": "Titres de section précédés d'un numéro 01, 02, 03 en ambre, "
                      "sur une ligne avec le sous-titre",
    "places-joueurs": "Quatre cases de joueurs qui se remplissent au clic pour "
                      "rejoindre un match",
    "echelle-niveaux": "Échelle de niveaux cliquable qui révèle une description "
                       "franche par cran",
    "regles-ecrites": "Bandeau de règles du club en colonnes, annulation, absence, "
                      "retard",
}

# --------------------------------------------------------------------------- #
# Le journal : ce qui a réellement été livré, dans l'ordre
# --------------------------------------------------------------------------- #

JOURNAL = [
    {
        "page": "meca-02",
        "date": "2026-08-31",
        "metier": "industrie",
        "objet": "le plan d'atelier",
        "dispositifs": ["entete-ecusson", "chapeau-trait", "titre-condense",
                        "cartouche-chiffres", "piece-technique-2", "cartes-numerotees",
                        "faux-google", "suite-numerotee", "vrai-invente",
                        "photos-etiquetees", "citation-filet", "compteur-avance"],
    },
    {
        "page": "padel-presquile",
        "date": "2026-08-31",
        "metier": "sport",
        "objet": "un site avec une section réservation (VERSION ABANDONNÉE)",
        "dispositifs": ["entete-ecusson", "chapeau-trait", "titre-condense",
                        "piece-technique-2", "cartes-numerotees", "faux-google",
                        "suite-numerotee", "vrai-invente"],
    },
    {
        "page": "padel-presquile-v2",
        "date": "2026-08-31",
        "metier": "sport",
        "objet": "le tableau d'affichage lui-même, plein cadre, sans page d'accueil",
        # Aucun dispositif du catalogue : c'est le premier essai construit sous
        # interdiction. Ce qu'elle invente est consigné ci-dessous pour être
        # interdit à son tour.
        "dispositifs": ["bandeau-billet", "rail-jours", "ticket-glissant",
                        "verso-recu", "notes-lettres"],
    },
    {
        "page": "padel-presquile-v3",
        "date": "2026-08-31",
        "metier": "sport",
        "objet": "le club entier : réserver, trouver un quatrième, se situer",
        # Recherche faite avant de construire : le manque de quatrieme joueur est
        # le premier obstacle du padel, les niveaux 3 a 7 sont incompris, et les
        # clubs souffrent des no-shows. Ces trois constats commandent la structure.
        "dispositifs": ["bandeau-billet", "rail-jours", "ticket-glissant",
                        "verso-recu", "notes-lettres", "tete-numerotee",
                        "places-joueurs", "echelle-niveaux", "regles-ecrites"],
    },
]

FENETRE = 3  # un dispositif utilisé est interdit sur les N maquettes suivantes


def interdits(depuis=None):
    """Les dispositifs interdits pour la prochaine maquette.

    `depuis` : nom de page à exclure du calcul, quand on refait une page déjà
    au journal.
    """
    recents = [e for e in JOURNAL if e["page"] != depuis][-FENETRE:]
    vus = {}
    for e in recents:
        for d in e["dispositifs"]:
            vus.setdefault(d, []).append(e["page"])
    return vus


def bloc_markdown(depuis=None):
    """La section à coller dans le dossier, avant de construire."""
    vus = interdits(depuis)
    L = ["## Dispositifs INTERDITS sur cette maquette", ""]
    if not vus:
        a = "Aucun, le journal est vide. Tout est permis, et tout sera consigné."
        L += [a, ""]
        return "\n".join(L)

    L.append(f"Un dispositif utilisé est interdit sur les {FENETRE} maquettes "
             f"suivantes. Pas « à éviter » : interdit. Sinon il revient toujours.")
    L.append("")
    for d, pages in sorted(vus.items(), key=lambda x: -len(x[1])):
        L.append(f"- **{CATALOGUE.get(d, d)}** · déjà sur {', '.join(sorted(set(pages)))}")
    L.append("")
    L.append("### La règle qui remplace le gabarit")
    L.append("")
    L.append("**La page EST l'objet du métier, elle n'est pas un site qui en parle.** "
             "Un club de padel, sa page est un écran de réservation. Un atelier, sa "
             "page est un plan. Un caviste, sa page est une étagère. Cherche l'objet "
             "que ce métier manipule tous les jours, et fais-en la page entière. Le "
             "reste s'organise autour, ou disparaît.")
    L.append("")
    if JOURNAL:
        L.append("**Structures déjà employées, à ne pas rejouer :** "
                 + " · ".join(f"{e['page']} = {e['objet']}" for e in JOURNAL[-FENETRE:])
                 + ".")
        L.append("")
    return "\n".join(L)


def enregistre(page, metier, objet, dispositifs, date=None):
    """Ajoute une maquette au journal. À faire APRÈS livraison, pas avant."""
    from datetime import date as _d
    JOURNAL.append({"page": page, "date": date or _d.today().isoformat(),
                    "metier": metier, "objet": objet, "dispositifs": dispositifs})
    return JOURNAL[-1]


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    depuis = sys.argv[1] if len(sys.argv) > 1 else None
    print(bloc_markdown(depuis))
    print("---")
    print("Journal :")
    for e in JOURNAL:
        print(f"  {e['date']}  {e['page']:22} {e['metier']:12} "
              f"{len(e['dispositifs'])} dispositifs  ({e['objet']})")
