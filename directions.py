# -*- coding: utf-8 -*-
"""directions.py — une direction visuelle par métier, pour ne jamais se répéter.

Le problème que ça règle. À force de livrer vite, toutes les maquettes finissent
par se ressembler : même fond sombre, même accent, même grille. Un prospect ne
le voit pas, mais nous si, et surtout ça produit des pages qui ne racontent pas
le métier du client.

Ce fichier n'est pas une bibliothèque de gabarits. Il ne contient aucun code de
mise en page, et c'est délibéré : ce qu'on recopie d'une fois sur l'autre, c'est
la rigueur, jamais la forme. Il contient trois choses par métier :

  - LE CLICHÉ : ce que fait tout le monde, donc ce qu'on ne fait pas
  - LA DIRECTION : d'où vient la forme, tirée du métier lui-même
  - LA PIÈCE : le morceau technique à construire, celui qu'un thème ne sort pas

Et il garde la mémoire de ce qui a déjà été livré, pour ne pas refaire deux fois
la même chose à deux clients du même secteur.

    python directions.py restaurant
    python directions.py "atelier d'usinage de précision"
"""

import re
import sys
import unicodedata


def _norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# --------------------------------------------------------------------------- #
# Les directions, par métier
# --------------------------------------------------------------------------- #

DIRECTIONS = [
    {
        "cle": "industrie",
        "nom": "Industrie, usinage, métallurgie, sous-traitance",
        "mots": ["usinage", "mecanique", "tournage", "fraisage", "metallurgie",
                 "chaudronnerie", "forge", "soudure", "industriel", "atelier",
                 "sous-traitance", "decoupe", "tolerie", "outillage", "cnc"],
        "cliche": "Fond bleu nuit, dégradé, photo d'engrenage en banque d'images, "
                  "le mot « innovation » en gros. Toutes les agences font ça, et ça "
                  "ne dit rien de l'atelier.",
        "direction": "Le vocabulaire du plan : cotations, hachures de coupe, "
                     "cartouche, numéros de repère, tolérances. Un atelier est un "
                     "endroit clair et poussiéreux, pas une salle serveur. Une seule "
                     "couleur, celle des marquages de sécurité.",
        "piece": "Un procédé qui leur appartient, animé au défilement : découpe au "
                 "fil, profil qui se révolutionne au tour, pièce qui se dessine en "
                 "SVG coté. Jamais une roue dentée qui tourne.",
        "preuve": "Le parc machines poste par poste, matières, tolérances. C'est ce "
                  "qu'un donneur d'ordre lit en premier et ce que personne n'affiche.",
        "faits": ["MECA 02 (fil, plan sombre)", "Outils PAM (forge)",
                  "LS Métal", "Delta Usinage"],
    },
    {
        "cle": "restauration",
        "nom": "Restaurant, brasserie, food",
        "mots": ["restaurant", "brasserie", "bistrot", "pizzeria", "traiteur",
                 "creperie", "food", "cuisine", "burger", "naan", "kebab",
                 "boulangerie", "patisserie", "cafe", "bar", "glacier"],
        "cliche": "Photo de plat en plein écran, filtre chaud, bouton « Réserver » "
                  "orange, carte en PDF illisible sur téléphone. Le site de chaîne.",
        "direction": "La carte elle-même comme objet graphique : typographie de "
                     "menu, ardoise, tampon, papier kraft, prix alignés au filet. "
                     "Le lieu se raconte par ce qu'on y mange, pas par un carrousel.",
        "piece": "La carte lisible au pouce, sans PDF, avec filtres réels "
                 "(végétarien, halal, sans gluten) et les allergènes. Ou le parcours "
                 "de réservation en trois gestes, montré en fonctionnement.",
        "preuve": "Les horaires justes, l'adresse cliquable, le téléphone en un tap. "
                  "80 % des recherches se font sur mobile, à moins d'une heure du repas.",
        "faits": ["Le Phare", "Côte Mer", "Plouf Cancale", "Petite Émeraude",
                  "Café de la Bourse", "Monts Chipiron"],
    },
    {
        "cle": "hebergement",
        "nom": "Hôtel, chambres d'hôtes, gîte, camping",
        "mots": ["hotel", "chambre d'hote", "chambres d hotes", "gite", "camping",
                 "hebergement", "auberge", "location saisonniere", "jacuzzi", "spa"],
        "cliche": "Diaporama de chambres vides, widget de réservation d'un tiers "
                  "qui casse le design, et « bienvenue dans notre établissement ».",
        "direction": "Le lieu et son dehors : lumière du matin, matière des murs, "
                     "distance à la mer ou au sentier. Ce qu'on achète, c'est un "
                     "séjour dans un endroit, pas une chambre.",
        "piece": "La disponibilité réelle, montrée sans quitter la page. Ou une "
                 "carte des environs annotée à la main par le propriétaire.",
        "preuve": "Le prix de départ visible. Une chambre sans prix affiché fait "
                  "partir la moitié des visiteurs.",
        "faits": ["Ombelle", "Le Cancalais"],
    },
    {
        "cle": "artisan",
        "nom": "Artisan du bâtiment, BTP, paysagiste",
        "mots": ["macon", "menuisier", "plombier", "electricien", "couvreur",
                 "charpente", "paysagiste", "btp", "renovation", "carreleur",
                 "peintre", "terrassement", "artisan", "chauffagiste"],
        "cliche": "Bandeau avec un casque de chantier, « devis gratuit » en jaune, "
                  "et une galerie de photos floues prises au téléphone.",
        "direction": "L'avant-après, traité comme une preuve et non comme une "
                     "galerie. Matière brute, plan de coupe, échelle humaine.",
        "piece": "Le glissement avant-après au doigt sur un vrai chantier à eux. "
                 "Ou le chiffrage indicatif en trois questions.",
        "preuve": "Les assurances, la zone d'intervention réelle en kilomètres, et "
                  "le délai moyen de rappel. Ce sont les trois peurs du client.",
        "faits": [],
    },
    {
        "cle": "profession_liberale",
        "nom": "Avocat, expert-comptable, cabinet de conseil, notaire",
        "mots": ["avocat", "juridique", "notaire", "expert-comptable", "comptable",
                 "cabinet", "conseil", "consultant", "audit", "fiscal", "huissier"],
        "cliche": "Colonnes de temple grec, poignée de main, bleu marine, et une "
                  "photo d'équipe en costume devant une bibliothèque.",
        "direction": "La rigueur d'un document : filets fins, hiérarchie stricte, "
                     "beaucoup de blanc, une seule famille typographique bien menée. "
                     "La sobriété est ici un argument, pas une absence d'idée.",
        "piece": "Le premier rendez-vous démystifié : ce qu'il faut apporter, ce qui "
                 "se passe, combien de temps. Ou un simulateur d'éligibilité honnête.",
        "preuve": "Les domaines traités et surtout ceux qui ne le sont pas. Un "
                  "cabinet qui dit non à quelque chose est crédible sur le reste.",
        "faits": [],
    },
    {
        "cle": "sante",
        "nom": "Médical, dentaire, esthétique, bien-être",
        "mots": ["medical", "dentiste", "dentaire", "medecin", "kine", "osteo",
                 "esthetique", "sophrologue", "psychologue", "therapeute",
                 "cabinet medical", "podologue", "orthodontie", "veterinaire"],
        "cliche": "Bleu ciel, dégradé pastel, photo de mains jointes, feuille verte, "
                  "et le mot « bien-être » répété quatre fois.",
        "direction": "Le calme obtenu par la structure, pas par la couleur : "
                     "beaucoup d'air, une échelle typographique douce, aucun "
                     "mouvement brusque. La réassurance passe par la clarté du parcours.",
        "piece": "La prise de rendez-vous réelle, en trois gestes, sans compte à "
                 "créer. C'est le seul moment qui compte.",
        "preuve": "Conventionnement, tarifs, accès et stationnement. Les questions "
                  "qu'on n'ose pas poser au téléphone.",
        "faits": [],
    },
    {
        "cle": "immobilier",
        "nom": "Agence immobilière, promotion, gestion",
        "mots": ["immobilier", "agence immo", "promoteur", "syndic", "location",
                 "vente appartement", "maison", "foncier", "gestion locative"],
        "cliche": "Barre de recherche sur une photo de villa au coucher du soleil, "
                  "et des cartes de biens toutes identiques.",
        "direction": "Le plan et le quartier plutôt que la façade. Ce qu'on achète, "
                     "c'est une surface, une orientation et un voisinage.",
        "piece": "Le plan interactif d'un bien, ou la carte du secteur avec les "
                 "vrais temps de trajet. Quelque chose qu'un portail ne donne pas.",
        "preuve": "Les honoraires, affichés. C'est obligatoire et presque personne "
                  "ne le fait proprement.",
        "faits": [],
    },
    {
        "cle": "commerce",
        "nom": "E-commerce, boutique, marque produit",
        "mots": ["e-commerce", "boutique en ligne", "shopify", "woocommerce",
                 "prestashop", "vente en ligne", "marketplace", "panier", "produit"],
        "cliche": "Grille de produits identique à celle de tous les thèmes Shopify, "
                  "bandeau de livraison gratuite qui clignote, avis en carrousel.",
        "direction": "Le produit traité comme un objet unique : détail, matière, "
                     "échelle, fabrication. Moins de produits visibles à la fois, "
                     "beaucoup plus dits sur chacun.",
        "piece": "La vue produit qui montre ce qu'une photo ne montre pas : rotation, "
                 "zoom sur la matière, comparaison de taille avec un objet connu.",
        "preuve": "D'où ça vient, qui le fabrique, en combien de temps ça arrive. "
                  "Les trois questions qui font abandonner un panier.",
        "faits": ["Lysara (joaillerie, gemme WebGL)"],
    },
    {
        "cle": "sport",
        "nom": "Salle de sport, club, coach, événement sportif",
        "mots": ["salle de sport", "fitness", "crossfit", "coach sportif", "club",
                 "marathon", "course", "trail", "musculation", "yoga", "danse",
                 "association sportive"],
        "cliche": "Photo de quelqu'un qui soulève une barre en noir et blanc, "
                  "compteur qui monte, et « dépassement de soi ».",
        "direction": "Le vocabulaire rétro du sport : écusson, trame de maillot, "
                     "dossard, chronomètre mécanique, typographie de programme des "
                     "années 70. Exécution moderne, vocabulaire ancien.",
        "piece": "Le chrono ou le dossard animé, le parcours tracé sur une carte, "
                 "le planning des cours réellement lisible sur téléphone.",
        "preuve": "Les horaires exacts, le tarif, et comment on essaie une première "
                  "fois sans s'engager.",
        "faits": ["FitBreizh 29 (écusson, chrono)", "Marathon des Herbiers"],
    },
    {
        "cle": "auto",
        "nom": "Garage, carrosserie, concession, transport",
        "mots": ["garage", "carrosserie", "mecanicien auto", "pneu", "concession",
                 "transport", "logistique", "poids lourd", "vehicule", "flotte"],
        "cliche": "Voiture rouge sur fond noir avec un reflet, damier de course, "
                  "et « votre satisfaction est notre priorité ».",
        "direction": "L'atelier réel et la fiche d'intervention : numéro d'ordre, "
                     "temps passé, pièces changées. La transparence est l'argument "
                     "du secteur parce que la défiance y est maximale.",
        "piece": "Le devis en ligne par modèle, ou le suivi d'intervention étape "
                 "par étape.",
        "preuve": "Les tarifs horaires, les marques traitées, le véhicule de prêt.",
        "faits": [],
    },
    {
        "cle": "assoc",
        "nom": "Association, collectivité, culture",
        "mots": ["association", "mairie", "collectivite", "musee", "festival",
                 "culturel", "benevole", "adherent", "salle de spectacle", "theatre"],
        "cliche": "Logo compressé en haut à gauche, menu à douze entrées, et un "
                  "agenda en tableau illisible sur téléphone.",
        "direction": "L'affiche : composition forte, une image, une date, un lieu. "
                     "La culture se communique par l'affiche depuis un siècle, pas "
                     "par une grille de cartes.",
        "piece": "L'agenda qui se lit d'un coup d'œil et l'adhésion en trois champs.",
        "preuve": "Qui fait quoi, combien ça coûte, et comment on rejoint.",
        "faits": ["La Chapelle Hospitalité"],
    },
]

GENERIQUE = {
    "cle": "generique",
    "nom": "Métier non reconnu",
    "cliche": "Le gabarit d'agence : grand titre, trois colonnes d'icônes, "
              "témoignages, bandeau de contact.",
    "direction": "Cherche l'objet, le geste ou le document que ce métier manipule "
                 "tous les jours, et fais-en la forme de la page. S'il n'y a pas "
                 "d'objet, il y a toujours un document.",
    "piece": "Ce que le client fait vingt fois par jour et que son site ne montre "
             "nulle part.",
    "preuve": "Les trois questions qu'on lui pose au téléphone avant d'acheter.",
    "faits": [],
}


def trouver(texte):
    """La direction qui colle au métier décrit, ou la générique."""
    hay = _norm(texte)
    meilleur, score_max = None, 0
    for d in DIRECTIONS:
        score = sum(1 for m in d["mots"] if _norm(m) in hay)
        if score > score_max:
            meilleur, score_max = d, score
    return meilleur or GENERIQUE


def bloc_markdown(texte):
    """La section à coller dans un dossier de prospect."""
    d = trouver(texte)
    L = ["## Direction visuelle proposée", "",
         f"**Métier reconnu :** {d['nom']}", ""]
    L.append(f"**Le cliché, donc ce qu'on ne fait pas.** {d['cliche']}")
    L.append("")
    L.append(f"**La direction.** {d['direction']}")
    L.append("")
    L.append(f"**La pièce technique à construire.** {d['piece']}")
    L.append("")
    L.append(f"**Ce qui fait la preuve.** {d['preuve']}")
    L.append("")
    if d.get("faits"):
        L.append("**Déjà livré dans ce secteur, à ne pas refaire à l'identique :** "
                 + ", ".join(d["faits"]) + ".")
        L.append("")
    L.append("> Ces trois lignes ne sont pas un gabarit. Elles disent d'où part la "
             "forme. La mise en page se dessine à chaque fois, sinon on retombe "
             "exactement dans le problème qu'on essaie de fuir.")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("Métiers couverts :")
        for d in DIRECTIONS:
            print(f"  {d['cle']:22} {d['nom']}")
        raise SystemExit(0)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(bloc_markdown(" ".join(sys.argv[1:])))
