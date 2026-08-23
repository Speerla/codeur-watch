# Veille Codeur.com

Détecte les nouveaux projets Codeur qui correspondent à Speerla, les score, rédige un
brouillon de réponse à partir du brief, et envoie le tout par email.

Objectif : arriver sur le projet avec une réponse déjà écrite pendant que les autres
découvrent l'annonce.

## Source

`https://www.codeur.com/projects.rss` : flux public, sans compte, 35 derniers projets,
avec titre, lien, date, budget, catégories et début du brief. Le flux accepte un
paramètre de recherche : `?q=refonte site`.

## Utilisation

```bash
python watch.py                          # nouveautés depuis la dernière passe
python watch.py --loop 120 --max-age 3   # veille continue, toutes les 2 minutes
python watch.py --all --min-score 12     # rejoue le backlog, seuil dur
python watch.py --notify                 # envoie le digest par email
```

Ou simplement double-cliquer sur `veille.bat` (boucle 2 min + email).

Options : `--min-score` (défaut 6), `--min-budget` en euros (défaut 500),
`--max-age` en heures, `--all` (ignore l'état), `--loop` en secondes, `--notify`.

`state.json` retient les projets déjà signalés : jamais deux alertes pour le même projet.

## Les trois pièces

| Fichier | Rôle |
| --- | --- |
| `watch.py` | lit le flux, dédoublonne, score, filtre |
| `draft.py` | rédige le brouillon de réponse à partir du brief |
| `notify.py` | envoie le digest par email via Resend |

### Scoring

Mots positifs pondérés (refonte, site vitrine, e-commerce, WordPress, Next.js,
web design...), mots négatifs à -4 (community management, rédaction, jeu vidéo,
crypto, saisie de données...), bonus budget (+2 dès 1 000 €, +3 dès 5 000 €),
malus -3 sur « Moins de 500 € ». Seuil conseillé : 8.

### Brouillon

Le brouillon cite une phrase du brief, s'adapte au stack détecté (WordPress, Shopify,
Wix...), aux besoins repérés (multilingue, paiement, SEO, mobile, réservation...) et
au fait que ce soit une refonte ou une création. Il n'invente jamais de référence
client ni de chiffre. À relire avant envoi.

## Clé Resend

En local, la clé est lue automatiquement dans `../../site/.env.vercel.local`
(récupérée avec `vercel env pull` depuis le projet speerla). En CI, elle arrive
par les secrets GitHub.

## Veille automatique sur le PC (active)

Une tâche planifiée Windows tourne déjà toutes les 5 minutes, sans fenêtre :

```
nom       : Speerla - Veille Codeur
commande  : pythonw.exe runner.py
journal   : veille.log
```

```bash
schtasks /query /tn "Speerla - Veille Codeur"    # état et prochaine exécution
schtasks /run   /tn "Speerla - Veille Codeur"    # forcer une passe
schtasks /end   /tn "Speerla - Veille Codeur"    # stopper la passe en cours
schtasks /delete /tn "Speerla - Veille Codeur"   # tout retirer
```

Elle ne tourne évidemment que quand le PC est allumé. Pour du vrai 24/7, voir ci dessous.

## Veille 24/7 avec GitHub Actions

Le workflow `.github/workflows/veille.yml` tourne toutes les 5 minutes sur les runners
GitHub. Il reste une mise en route à faire une seule fois, parce qu'elle demande un
navigateur et une clé API : double-cliquer sur `setup-github.bat`.

Le script autorise `gh` à pousser des workflows, envoie le workflow, puis dépose les
trois secrets sur le repo `Speerla/codeur-watch`.

Le cron GitHub peut se décaler de quelques minutes aux heures chargées. C'est pour ça
que la fenêtre est réglée sur 3 heures : un projet publié pendant un retard de runner
est quand même signalé, et `state.json` empêche le doublon.

## Limites connues

- Répondre à un projet sur Codeur exige un abonnement freelance à partir de
  31,90 € HT/mois, plus 4 % de commission sur les projets gagnés.
- Les recherches `?q=` sont triées par pertinence, pas par date : c'est `--max-age`
  qui garantit la fraîcheur en veille temps réel.
- Le flux public ne donne que le début du brief et jamais le contact du client.
- Malt n'a pas d'équivalent : aucune annonce publique, les clients contactent
  directement les freelances via le matching interne. Rien à surveiller là-bas.
