# Veille Codeur.com

Detecte les nouveaux projets Codeur qui correspondent a Speerla, les score, et
affiche un digest exploitable dans la seconde.

## Source
`https://www.codeur.com/projects.rss` : flux public, sans compte, 35 derniers
projets, avec titre, lien, date, budget, categories et debut du brief.
Le flux accepte un parametre de recherche : `?q=refonte site`.

## Utilisation
```bash
python watch.py                          # nouveautes depuis la derniere passe
python watch.py --loop 120 --max-age 12  # veille continue (toutes les 2 min)
python watch.py --all --min-score 10     # rejoue le backlog, seuil dur
```

Options : `--min-score` (defaut 6), `--min-budget` (defaut 500 EUR),
`--max-age` en heures, `--all` (ignore l'etat), `--loop` en secondes.

`state.json` retient les projets deja vus : un projet n'est annonce qu'une fois.

## Scoring
Mots positifs ponderes (refonte, site vitrine, e-commerce, WordPress, Next.js,
web design...), mots negatifs a -4 (community management, redaction, jeu video,
crypto, saisie de donnees...), bonus budget (+2 des 1 000 EUR, +3 des 5 000 EUR),
malus -3 sur "Moins de 500 EUR".

## Limites connues
- Repondre a un projet sur Codeur exige un abonnement freelance (a partir de
  31,90 EUR HT/mois) plus 4 % de commission sur les projets gagnes.
- Les recherches `?q=` sont triees par pertinence, pas par date : utiliser
  `--max-age` pour la veille temps reel.
- Le flux public ne donne que le debut du brief et jamais le contact client.
