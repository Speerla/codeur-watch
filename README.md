# Veille Codeur.com

Détecte les nouveaux projets Codeur qui correspondent à Speerla, les score, rédige un
brouillon de réponse à partir du brief, et envoie le tout par email.

Python, aucune dépendance, bibliothèque standard uniquement. Trois fichiers, un flux
RSS public, et une tâche planifiée. Licence MIT.

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

Le workflow `.github/workflows/veille.yml` est en ligne et actif sur
`Speerla/codeur-watch`. Il tourne toutes les 5 minutes entre 7h et 23h (heure de Paris).

Il manque seulement les secrets : double-cliquer sur `setup-github.bat`, coller la clé
Resend quand il la demande. Ensuite la veille tourne même PC éteint.

### Le planificateur de GitHub ne tient pas la cadence

Mesure faite le 31 aout 2026 sur les vingt dernieres executions declenchees par
`schedule`, alors que le cron demandait 20 minutes :

```
30/08 23:51   30/08 21:33   30/08 18:34   30/08 14:59   30/08 10:25
29/08 21:56   29/08 19:20   29/08 15:44   29/08 11:33   29/08 01:01
```

Entre **1 h et 8 h** d'ecart. Toutes en succes, aucune en echec : GitHub ne
plante pas, il declasse. C'est documente et sans recours. Sur une veille ou un
projet ramasse jusqu'a 7 offres par heure, ce retard coute la mission.

### Le declencheur HTTP

On garde GitHub pour le travail et on lui retire l'horloge. Le workflow ecoute
`repository_dispatch`, et n'importe quel service de cron exterieur le reveille :

```bash
curl -X POST https://api.github.com/repos/Speerla/codeur-watch/dispatches \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Accept: application/vnd.github+json" \
  -d '{"event_type":"veille"}'
```

Teste le 31/08/2026 : le run demarre dans la seconde, contre 6 h d'attente pour
la derniere execution planifiee.

**Le jeton.** Un PAT *fine-grained*, cree sur
`github.com/settings/personal-access-tokens/new` :

- Repository access : **Only select repositories**, et seulement `codeur-watch`
- Permissions : **Contents = Read and write**, rien d'autre
- Expiration : 90 jours, a renouveler

Il donne le droit d'ecrire dans ce depot et uniquement celui-la. Ne jamais
utiliser un token classique a portee `repo`, qui ouvrirait tous les depots du
compte a un service tiers.

**L'horloge.** N'importe quel cron externe qui sait faire un POST avec des
en-tetes. `cron-job.org` le fait gratuitement a la minute pres. Une tache, la
methode POST, les deux en-tetes ci-dessus, le corps `{"event_type":"veille"}`,
toutes les 5 minutes.

Le `schedule` reste dans le fichier comme filet : si le declencheur externe
tombe, la veille continue de tourner, en retard, mais elle tourne.


## Limites connues

- Répondre à un projet sur Codeur exige un abonnement freelance à partir de
  31,90 € HT/mois, plus 4 % de commission sur les projets gagnés.
- Les recherches `?q=` sont triées par pertinence, pas par date : c'est `--max-age`
  qui garantit la fraîcheur en veille temps réel.
- Le flux public ne donne que le début du brief et jamais le contact du client.
- Malt n'a pas d'équivalent : aucune annonce publique, les clients contactent
  directement les freelances via le matching interne. Rien à surveiller là-bas.
