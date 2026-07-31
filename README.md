# shorts-tools — pipeline pour shorts de commentaires chantés

Objectif final : une chaîne de commande qui génère des shorts d'une minute
composés de commentaires YouTube drôles chantés/lus en musique, prêts à
monter dans CapCut.

## Pipeline

0. **`find_trending.py`** — repère chaque jour les vidéos YouTube et posts
   Reddit tendance (candidats sources), filtrés par nombre de commentaires
   minimum.
1. **`get_comments.py`** / **`get_reddit_comments.py`** — récupère les
   commentaires les plus populaires d'une vidéo YouTube ou d'un post Reddit.
   Les deux produisent le même format de sortie (`author`/`text`/`likes`),
   interchangeable pour la suite du pipeline.
2. **`select_comments.py`** — filtre le spam et sélectionne les commentaires les
   mieux likés dans un budget de durée cible (~1 minute).
3. *(à venir)* génération audio chantée, montage vidéo, export.

```bash
python find_trending.py --out trending.json
# choisir une URL dans trending.json, puis :

python get_comments.py "https://youtu.be/XXXXXXXXXXX" --format json --out comments.json
# ou, source Reddit :
python get_reddit_comments.py "https://www.reddit.com/r/AskReddit/comments/XXXXXXX/" --format json --out comments.json

python select_comments.py comments.json --target-duration 55 --out selection.json
```

`selection.json` contient les commentaires retenus, dans l'ordre, avec leur
durée estimée — prêt à servir d'entrée à l'étape de génération audio.

---

# find_trending.py — repérer les tendances du jour (YouTube + Reddit)

Interroge les tendances YouTube (`videos.list?chart=mostPopular`) et les tops
du jour de plusieurs subreddits (`/r/{sub}/top?t=day`) pour produire une
liste de candidats sources, triés par nombre de commentaires décroissant.
Réutilise les identifiants YouTube et Reddit déjà configurés pour
`get_comments.py` / `get_reddit_comments.py`.

```bash
python find_trending.py --out trending.json
# personnaliser les sources :
python find_trending.py --subreddits memes,funny,ProgrammerHumor --min-comments 100 --top 15 --out trending.json
```

Options :
- `--youtube-region` : code région pour les tendances YouTube (défaut `US`)
- `--youtube-category` : ID de catégorie YouTube à filtrer (ex : `23` = Comedy, `24` = Entertainment)
- `--youtube-max` : nombre max de vidéos YouTube à considérer (défaut 25)
- `--subreddits` : liste de subreddits séparés par des virgules (défaut : `memes,funny,facepalm,AskReddit,mildlyinfuriating`)
- `--reddit-limit` : nombre de posts à considérer par subreddit (défaut 25)
- `--min-comments` : seuil minimum de commentaires pour retenir un candidat (défaut 50)
- `--top N` : nombre total de candidats à garder au final (défaut 20)
- `--out fichier.json` : écrit le résultat dans un fichier

Chaque candidat contient `source` (`youtube`/`reddit`), `id`, `title`, `url`,
`comment_count`, et un champ spécifique à la source (`view_count` pour
YouTube, `score`/`subreddit` pour Reddit) — l'`url` est prête à être passée
à `get_comments.py` ou `get_reddit_comments.py`.

⚠️ Reddit a fermé l'accès self-service à son API (voir "Limites à
connaître" plus bas) : sans `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET`, le
script fonctionne en mode YouTube uniquement (log d'info, pas d'erreur).

⚠️ Les tendances brutes mélangent contenu drôle et actualité sérieuse : le
filtre `--min-comments` aide, mais la sélection finale des candidats reste
à valider avant de lancer le reste du pipeline.

---

# get_comments.py — récupérer les commentaires les plus populaires d'une vidéo YouTube

Script pour le format "lecture de commentaires en musique". Récupère les commentaires
d'une vidéo, triés par likes, prêts à copier dans CapCut.

## 1. Obtenir une clé API (gratuit)

1. Aller sur https://console.cloud.google.com/
2. Créer un projet (ou en choisir un existant)
3. Menu "API et services" → "Bibliothèque" → chercher **YouTube Data API v3** → l'activer
4. "API et services" → "Identifiants" → "Créer des identifiants" → **Clé API**
5. Copier la clé générée

Quota gratuit : 10 000 unités/jour. Une recherche de commentaires coûte 1 unité par page
de 100 commentaires — largement suffisant pour un usage quotidien.

## 2. Installer

Aucune dépendance externe : le script utilise uniquement la bibliothèque standard Python
(3.7+). Rien à installer.

## 3. Utiliser

```bash
# Windows (cmd)
set YOUTUBE_API_KEY=votre_cle_ici
python get_comments.py "https://www.youtube.com/watch?v=XXXXXXXXXXX" --top 20 --out commentaires.txt

# Ou sans variable d'environnement
python get_comments.py "https://youtu.be/XXXXXXXXXXX" --key votre_cle_ici --top 15
```

Options :
- `--top N` : nombre de commentaires à garder, triés par likes (défaut 20)
- `--min-likes N` : ignore les commentaires en dessous de ce seuil (défaut 0)
- `--out fichier.txt` : écrit le résultat dans un fichier au lieu de l'afficher
- `--format text|json` : texte lisible (défaut) ou JSON structuré, à utiliser
  pour chaîner avec `select_comments.py`

Le script accepte une URL complète, une URL courte (youtu.be), un lien Shorts, ou
directement l'ID de la vidéo (11 caractères).

---

# get_reddit_comments.py — récupérer les commentaires les plus populaires d'un post Reddit

Alternative à `get_comments.py` pour une source Reddit. Même logique (tri par
score, filtre `--min-likes`, `--top`, `--format text|json`) et même format de
sortie (`author`/`text`/`likes`) — les deux scripts sont interchangeables en
entrée de `select_comments.py`.

## 1. Obtenir des identifiants (gratuit)

1. Aller sur https://www.reddit.com/prefs/apps (connecté à votre compte Reddit)
2. "Create app" (ou "create another app")
3. Choisir le type **script**, remplir un nom et une description quelconques,
   mettre `http://localhost:8080` comme "redirect uri" (obligatoire mais inutilisé ici)
4. Une fois créée, noter le **client ID** (chaîne sous le nom de l'app) et le
   **secret**

Quota gratuit : 100 requêtes/minute pour un usage type "script" — largement
suffisant pour un usage quotidien.

## 2. Utiliser

```bash
# Windows (cmd)
set REDDIT_CLIENT_ID=votre_client_id
set REDDIT_CLIENT_SECRET=votre_secret
python get_reddit_comments.py "https://www.reddit.com/r/AskReddit/comments/XXXXXXX/titre/" --top 20 --out commentaires.txt

# Ou sans variables d'environnement
python get_reddit_comments.py "https://www.reddit.com/r/AskReddit/comments/XXXXXXX/" --client-id ID --client-secret SECRET --top 15
```

Le script accepte une URL de post complète ou directement l'ID du post (base36,
tel qu'il apparaît dans l'URL après `/comments/`).

---

# select_comments.py — sélectionner les commentaires pour un short

À partir du JSON produit par `get_comments.py --format json`, ce script filtre
le spam (liens, commentaires uniquement en emojis, trop courts), déduplique,
puis retient les commentaires les mieux likés jusqu'à épuiser un budget de
durée estimée (basé sur un débit de mots par minute, réglable).

```bash
python select_comments.py comments.json --target-duration 55 --out selection.json
# ou en pipe :
python get_comments.py "URL" --format json | python select_comments.py - --target-duration 55
```

Options :
- `--target-duration N` : durée cible en secondes pour l'ensemble des
  commentaires retenus (défaut 55, pour laisser une marge sur un short d'1 min)
- `--max-segments N` : nombre maximum de commentaires à retenir (défaut illimité)
- `--min-words N` : mots minimum par commentaire, filtre anti-spam (défaut 4)
- `--max-chars N` : caractères maximum par commentaire (défaut 220)
- `--wpm N` : débit estimé du chant/lecture en mots par minute, sert à estimer
  la durée de chaque commentaire (défaut 90 — à ajuster une fois le rendu
  audio réel disponible)
- `--out fichier.json` : écrit le résultat dans un fichier

Chaque commentaire retenu dans la sortie contient sa durée estimée
(`est_duration_sec`) et la durée cumulée (`cumulative_duration_sec`), pour
faciliter le calage avec l'étape audio suivante.

## Limites à connaître

- Sources supportées : YouTube et Reddit, toutes deux via leur API officielle
  publique. TikTok, Instagram et Facebook n'ont pas d'API publique permettant
  de lire les commentaires d'un post qui ne vous appartient pas (Graph API et
  TikTok Display/Research API ne couvrent que votre propre contenu, ou
  nécessitent un dossier de candidature recherche approuvé) — le scraping
  violerait leurs conditions d'utilisation, ce n'est donc volontairement pas
  supporté ici.
- **Reddit a fermé l'inscription self-service à son API** (annonce
  "Responsible Builder Policy", 2025) : créer une app "script" sur
  `reddit.com/prefs/apps` ne fonctionne plus pour les nouveaux comptes, une
  demande d'approbation est désormais nécessaire. `get_reddit_comments.py`
  et `find_trending.py` restent fonctionnels dès que des identifiants sont
  obtenus (compte déjà approuvé, ou demande acceptée), mais ne sont pas
  utilisables en self-service pour l'instant.
- Le tri "relevance" de YouTube mélange déjà popularité et pertinence ; le script retrie
  ensuite par nombre de likes brut pour privilégier les commentaires les plus drôles/aimés.
  Reddit trie nativement par score ("top").
- Les commentaires épinglés/désactivés ou les vidéos/posts avec commentaires fermés
  ne retourneront rien (erreur API explicite dans ce cas).
