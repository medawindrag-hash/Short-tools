# Changelog

Journal des changements effectués sur ce projet. Ce dossier n'est pas un
dépôt git : ce fichier est le seul moyen de faire un rollback manuel.
Entrées en ordre anté-chronologique (la plus récente en haut). Voir le
skill `changelog` (`.claude/skills/changelog/SKILL.md`) pour le gabarit
à utiliser.

## Entrées

### 2026-07-20 — Documentation de find_trending.py dans README.md
- **Fichier(s):** README.md
- **Type:** modification
- **Changement:** Ajout d'une étape "0." dans la section "## Pipeline"
  (mention de `find_trending.py` + exemple de commande), et ajout de la
  section "# find_trending.py — repérer les tendances du jour (YouTube +
  Reddit)" juste avant la section "# get_comments.py".
- **Rollback:** Retirer le point "0." de "## Pipeline" (renuméroter 1/2/3 →
  reste 1/2/3, pas de changement de numéros) et la ligne `python
  find_trending.py --out trending.json` + commentaire de l'exemple de
  commande, puis supprimer toute la section "# find_trending.py —
  repérer les tendances du jour (YouTube + Reddit)" (entre le `---` qui la
  précède et le `---` qui suit, juste avant "# get_comments.py").

### 2026-07-20 — Création de find_trending.py (découverte des tendances du jour)
- **Fichier(s):** find_trending.py
- **Type:** ajout
- **Changement:** Nouveau script qui interroge `videos.list?chart=mostPopular`
  (YouTube) et `/r/{sub}/top?t=day` (Reddit, pour une liste de subreddits
  configurable) afin de produire une liste de candidats sources (vidéos/posts
  tendance du jour), filtrés par nombre de commentaires minimum et triés par
  nombre de commentaires décroissant. Sortie JSON compatible en entrée de
  `get_comments.py`/`get_reddit_comments.py` (champ `url`). Testé
  hors-ligne : `parse_youtube_trending` et `parse_reddit_trending` (logique
  de filtrage, extraite pour être testable sans appel réseau) validés avec
  des réponses JSON factices imitant les APIs YouTube/Reddit ; `--help`
  vérifié ; pas de test réseau réel possible (aucune clé API dans cet
  environnement).
- **Rollback:** Supprimer le fichier `find_trending.py`.

### 2026-07-20 — Factorisation de l'authentification Reddit (reddit_auth.py)
- **Fichier(s):** reddit_auth.py (nouveau), get_reddit_comments.py (modifié)
- **Type:** ajout + modification
- **Changement:** Extraction de la logique d'authentification OAuth Reddit
  (`get_access_token`, `USER_AGENT`, `TOKEN_URL`) de `get_reddit_comments.py`
  vers un nouveau module `reddit_auth.py`, réutilisé par `find_trending.py`
  pour éviter de dupliquer cette logique une deuxième fois. Comportement
  inchangé (revérifié : `parse_comments_listing` toujours correct après le
  changement d'import).
- **Rollback:**
  1. Supprimer le fichier `reddit_auth.py`.
  2. Dans `get_reddit_comments.py`, remplacer :
     ```python
     import argparse
     import json
     import os
     import re
     import sys
     import urllib.request
     import urllib.parse
     import urllib.error

     from reddit_auth import get_access_token, USER_AGENT

     API_BASE = "https://oauth.reddit.com"
     ```
     par :
     ```python
     import argparse
     import base64
     import json
     import os
     import re
     import sys
     import urllib.request
     import urllib.parse
     import urllib.error

     TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
     API_BASE = "https://oauth.reddit.com"
     USER_AGENT = "shorts-tools/1.0 (comment fetcher for short-form video pipeline)"
     ```
     puis réinsérer la fonction `get_access_token` (identique à celle de
     `reddit_auth.py`) juste avant `def parse_comments_listing(data) -> list:`.

### 2026-07-20 — Documentation de Reddit comme source dans README.md
- **Fichier(s):** README.md
- **Type:** modification
- **Changement:** Mise à jour de la section "Pipeline" (mention de
  `get_reddit_comments.py`, exemple de commande), ajout de la section
  "# get_reddit_comments.py" (setup identifiants + usage), renommage de
  "## 4. select_comments.py" en titre top-level "# select_comments.py", et
  mise à jour de "Limites à connaître" (Reddit ajouté, TikTok/Instagram/
  Facebook explicitement écartés avec justification).
- **Rollback:** Retirer la mention de `get_reddit_comments.py` du point 1 de
  "## Pipeline" et de l'exemple de commande, supprimer toute la section
  "# get_reddit_comments.py — récupérer les commentaires les plus populaires
  d'un post Reddit" (entre le `---` qui la précède et le `---` qui suit),
  remettre "# select_comments.py" en "## 4. select_comments.py", et restaurer
  "## Limites à connaître" à sa version précédente :
  ```
  ## Limites à connaître

  - Fonctionne uniquement sur YouTube. Instagram et TikTok n'ont pas d'API publique
    équivalente pour les commentaires d'un post qui ne vous appartient pas — le scraping
    violerait leurs conditions d'utilisation.
  - Le tri "relevance" de YouTube mélange déjà popularité et pertinence ; le script retrie
    ensuite par nombre de likes brut pour privilégier les commentaires les plus drôles/aimés.
  - Les commentaires épinglés/désactivés ou les vidéos avec commentaires fermés ne
    retourneront rien (erreur API explicite dans ce cas).
  ```

### 2026-07-20 — Création de get_reddit_comments.py (source Reddit)
- **Fichier(s):** get_reddit_comments.py
- **Type:** ajout
- **Changement:** Nouveau script qui récupère les commentaires les plus
  populaires d'un post Reddit via l'API OAuth officielle (client credentials,
  app de type "script"), avec la même interface CLI et le même format de
  sortie (`author`/`text`/`likes`, `--format text|json`) que
  `get_comments.py`, pour être interchangeable en entrée de
  `select_comments.py`. Testé avec un jeu de données JSON factice imitant la
  structure de réponse de l'API Reddit (`parse_comments_listing`) : filtre
  correctement les commentaires supprimés/retirés et les stubs "more".
- **Rollback:** Supprimer le fichier `get_reddit_comments.py`.

### 2026-07-20 — Documentation du pipeline (get_comments.py + select_comments.py) dans README.md
- **Fichier(s):** README.md
- **Type:** modification
- **Changement:** Ajout d'une section "Pipeline" en tête de fichier (objectif
  final + étapes 1/2/3), d'une ligne décrivant `--format text|json` dans les
  options de `get_comments.py`, et d'une nouvelle section "4. select_comments.py"
  décrivant ses options.
- **Rollback:** Supprimer le bloc "## Pipeline" (et le séparateur `---`) ajouté
  juste avant le titre `# get_comments.py — récupérer...`, retirer la ligne
  `--format text|json : ...` de la liste d'options, et supprimer toute la
  section "## 4. select_comments.py — sélectionner les commentaires pour un short".
  Le fichier redevient alors identique à sa version où seul `get_comments.py`
  était documenté.

### 2026-07-20 — Création de select_comments.py (curation/sélection des commentaires)
- **Fichier(s):** select_comments.py
- **Type:** ajout
- **Changement:** Nouveau script qui prend en entrée le JSON de
  `get_comments.py --format json`, filtre le spam (liens, emojis seuls,
  commentaires trop courts), déduplique, puis sélectionne les commentaires
  les mieux likés jusqu'à un budget de durée estimée (`--target-duration`,
  `--wpm`) pour préparer l'étape "short chanté d'1 min".
- **Rollback:** Supprimer le fichier `select_comments.py`.

### 2026-07-20 — Ajout du format de sortie JSON à get_comments.py
- **Fichier(s):** get_comments.py
- **Type:** modification
- **Changement:** Ajout de l'option `--format {text,json}` (défaut `text`,
  comportement inchangé par défaut) pour permettre de chaîner la sortie vers
  `select_comments.py`.
- **Rollback:** Dans `main()`, retirer la ligne
  `parser.add_argument("--format", choices=["text", "json"], default="text", ...)`
  juste après la ligne `--out`, puis remplacer le bloc :
  ```python
  if args.format == "json":
      output = json.dumps(comments, ensure_ascii=False, indent=2)
  else:
      lines = []
      for i, c in enumerate(comments, 1):
          lines.append(f"{i}. [{c['likes']} likes] {c['author']} : {c['text']}")
      output = "\n\n".join(lines)
  ```
  par l'original :
  ```python
  lines = []
  for i, c in enumerate(comments, 1):
      lines.append(f"{i}. [{c['likes']} likes] {c['author']} : {c['text']}")

  output = "\n\n".join(lines)
  ```

### 2026-07-20 — Mise en place du skill de journalisation
- **Fichier(s):** .claude/skills/changelog/SKILL.md, CHANGELOG.md
- **Type:** ajout
- **Changement:** Création d'un skill Claude Code qui consigne chaque
  changement de fichier dans ce CHANGELOG afin de permettre un rollback
  manuel, en l'absence de dépôt git dans ce dossier.
- **Rollback:** Supprimer le dossier `.claude/skills/changelog/` et ce
  fichier `CHANGELOG.md`.
