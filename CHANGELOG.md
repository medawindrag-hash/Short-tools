# Changelog

Journal des changements effectués sur ce projet. Ce dossier n'est pas un
dépôt git : ce fichier est le seul moyen de faire un rollback manuel.
Entrées en ordre anté-chronologique (la plus récente en haut). Voir le
skill `changelog` (`.claude/skills/changelog/SKILL.md`) pour le gabarit
à utiliser.

## Entrées

### 2026-07-31 — Retrait complet de Reddit du pipeline
- **Fichier(s):** get_reddit_comments.py (supprimé), reddit_auth.py (supprimé), find_trending.py (modifié), README.md (modifié)
- **Type:** suppression + modification
- **Changement:** Reddit reste fermé en self-service (voir entrée précédente
  "Reddit rendu optionnel"), et l'utilisateur a demandé de retirer
  entièrement Reddit du pipeline plutôt que de le garder en option morte.
  Suppression de `get_reddit_comments.py` et `reddit_auth.py`, retrait de
  toute la logique Reddit dans `find_trending.py` (fetch/parse/args/merge),
  et mise à jour du README (pipeline, section find_trending.py, section
  get_reddit_comments.py supprimée, "Limites à connaître").
- **Rollback:**

  1. Recréer `get_reddit_comments.py` avec ce contenu :
  ```python
  #!/usr/bin/env python3
  """
  get_reddit_comments.py — Récupère et classe les commentaires les plus
  populaires d'un post Reddit via l'API officielle Reddit (OAuth, usage
  "script"). Sortie compatible avec select_comments.py (mêmes champs
  author/text/likes que get_comments.py).

  Usage :
      python get_reddit_comments.py <URL_ou_ID_post> [--top 20] [--min-likes 5] [--out fichier.txt]

  Nécessite un client OAuth Reddit de type "script" (gratuit), avec
  REDDIT_CLIENT_ID et REDDIT_CLIENT_SECRET définis en variables
  d'environnement, ou passés avec --client-id / --client-secret.

  Voir README.md pour la marche à suivre (création de l'app sur
  https://www.reddit.com/prefs/apps).
  """

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


  def extract_post_id(url_or_id: str) -> str:
      """Accepte une URL Reddit complète (post) ou un ID brut (base36, ex: 1abcde)."""
      url_or_id = url_or_id.strip()

      if re.fullmatch(r"[A-Za-z0-9]{4,10}", url_or_id):
          return url_or_id

      match = re.search(r"/comments/([A-Za-z0-9]{4,10})", url_or_id)
      if match:
          return match.group(1)

      raise ValueError(f"Impossible d'extraire l'ID du post depuis : {url_or_id}")


  def parse_comments_listing(data) -> list:
      """Extrait les commentaires de premier niveau depuis la réponse JSON de /comments/{id}.

      `data` est la structure telle que renvoyée par l'API (liste de deux
      Listings : [0] le post, [1] les commentaires). Séparé de fetch_comments
      pour pouvoir être testé sans appel réseau.
      """
      comments = []
      if len(data) < 2:
          return comments

      children = data[1].get("data", {}).get("children", [])
      for child in children:
          if child.get("kind") != "t1":
              continue
          c = child.get("data", {})
          author = c.get("author", "?")
          body = c.get("body", "").strip()
          if author == "[deleted]" or body in ("", "[deleted]", "[removed]"):
              continue
          comments.append({
              "author": author,
              "text": body,
              "likes": c.get("score", 0),
          })
      return comments


  def fetch_comments(post_id: str, token: str, max_total: int = 300) -> list:
      params = {
          "sort": "top",
          "limit": max_total,
          "depth": 1,
          "raw_json": 1,
      }
      url = f"{API_BASE}/comments/{post_id}?{urllib.parse.urlencode(params)}"

      request = urllib.request.Request(url)
      request.add_header("Authorization", f"Bearer {token}")
      request.add_header("User-Agent", USER_AGENT)

      try:
          with urllib.request.urlopen(request) as response:
              data = json.loads(response.read().decode("utf-8"))
      except urllib.error.HTTPError as e:
          body = e.read().decode("utf-8", errors="ignore")
          raise RuntimeError(f"Erreur API Reddit ({e.code}) : {body}") from e

      return parse_comments_listing(data)


  def main():
      parser = argparse.ArgumentParser(description="Récupère les commentaires les plus populaires d'un post Reddit.")
      parser.add_argument("post", help="URL ou ID du post Reddit")
      parser.add_argument("--top", type=int, default=20, help="Nombre de commentaires à garder (défaut : 20)")
      parser.add_argument("--min-likes", type=int, default=0, help="Filtre : score minimum (défaut : 0)")
      parser.add_argument("--client-id", default=None, help="Client ID Reddit (sinon lu depuis REDDIT_CLIENT_ID)")
      parser.add_argument("--client-secret", default=None, help="Client secret Reddit (sinon lu depuis REDDIT_CLIENT_SECRET)")
      parser.add_argument("--out", default=None, help="Fichier de sortie .txt (sinon affichage terminal uniquement)")
      parser.add_argument("--format", choices=["text", "json"], default="text", help="Format de sortie : texte lisible ou JSON structuré pour chaînage avec d'autres scripts (défaut : text)")
      args = parser.parse_args()

      client_id = args.client_id or os.environ.get("REDDIT_CLIENT_ID")
      client_secret = args.client_secret or os.environ.get("REDDIT_CLIENT_SECRET")
      if not client_id or not client_secret:
          print("Erreur : identifiants Reddit manquants. Définissez REDDIT_CLIENT_ID et REDDIT_CLIENT_SECRET, ou utilisez --client-id/--client-secret.", file=sys.stderr)
          print("Voir README.md pour créer une app Reddit (type \"script\") gratuite.", file=sys.stderr)
          sys.exit(1)

      try:
          post_id = extract_post_id(args.post)
      except ValueError as e:
          print(f"Erreur : {e}", file=sys.stderr)
          sys.exit(1)

      try:
          token = get_access_token(client_id, client_secret)
          comments = fetch_comments(post_id, token)
      except RuntimeError as e:
          print(f"Erreur : {e}", file=sys.stderr)
          sys.exit(1)

      comments = [c for c in comments if c["likes"] >= args.min_likes]
      comments.sort(key=lambda c: c["likes"], reverse=True)
      comments = comments[: args.top]

      if not comments:
          print("Aucun commentaire trouvé avec ces critères.")
          return

      if args.format == "json":
          output = json.dumps(comments, ensure_ascii=False, indent=2)
      else:
          lines = []
          for i, c in enumerate(comments, 1):
              lines.append(f"{i}. [{c['likes']} likes] {c['author']} : {c['text']}")
          output = "\n\n".join(lines)

      if args.out:
          with open(args.out, "w", encoding="utf-8") as f:
              f.write(output)
          print(f"{len(comments)} commentaires écrits dans {args.out}")
      else:
          print(output)


  if __name__ == "__main__":
      main()
  ```

  2. Recréer `reddit_auth.py` avec ce contenu :
  ```python
  #!/usr/bin/env python3
  """
  reddit_auth.py — Authentification OAuth Reddit partagée ("application only" /
  client credentials, lecture de contenu public uniquement), utilisée par
  get_reddit_comments.py et find_trending.py.
  """

  import base64
  import json
  import urllib.request
  import urllib.parse
  import urllib.error

  TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
  USER_AGENT = "shorts-tools/1.0 (comment fetcher for short-form video pipeline)"


  def get_access_token(client_id: str, client_secret: str) -> str:
      """Authentification OAuth "application only" (lecture de contenu public uniquement)."""
      credentials = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
      data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")

      request = urllib.request.Request(TOKEN_URL, data=data, method="POST")
      request.add_header("Authorization", f"Basic {credentials}")
      request.add_header("User-Agent", USER_AGENT)

      try:
          with urllib.request.urlopen(request) as response:
              payload = json.loads(response.read().decode("utf-8"))
      except urllib.error.HTTPError as e:
          body = e.read().decode("utf-8", errors="ignore")
          raise RuntimeError(f"Erreur d'authentification Reddit ({e.code}) : {body}") from e

      token = payload.get("access_token")
      if not token:
          raise RuntimeError(f"Réponse d'authentification Reddit inattendue : {payload}")
      return token
  ```

  3. Dans `find_trending.py`, réintégrer les imports/constantes/fonctions
  Reddit (`from reddit_auth import get_access_token, USER_AGENT`,
  `REDDIT_API_BASE`, `DEFAULT_SUBREDDITS`, `fetch_reddit_trending`,
  `parse_reddit_trending`) et les arguments/logique dans `main()`
  (`--subreddits`, `--reddit-limit`, `--reddit-client-id`,
  `--reddit-client-secret`, fetch conditionnel, `combined = youtube_results + reddit_results`)
  — voir l'entrée "2026-07-31 — Reddit rendu optionnel dans find_trending.py + doc à jour"
  ci-dessous pour le code exact de cette version.

  4. Dans README.md, réintégrer les mentions Reddit dans "## Pipeline"
  (point 1, exemple de commande), la section "# find_trending.py"
  (description, `--subreddits`, `--reddit-limit`, note sur le champ
  `source`), réajouter toute la section "# get_reddit_comments.py —
  récupérer les commentaires les plus populaires d'un post Reddit", et
  restaurer "## Limites à connaître" à sa version avec la mention Reddit
  fonctionnel + note de fermeture self-service (voir entrées précédentes).

### 2026-07-31 — Reddit rendu optionnel dans find_trending.py + doc à jour
- **Fichier(s):** find_trending.py, README.md
- **Type:** modification
- **Changement:** Reddit a fermé l'inscription self-service à son API
  (confirmé par l'utilisateur : la création d'app "script" sur
  reddit.com/prefs/apps boucle sur la page "Responsible Builder Policy"
  sans jamais créer l'app). `find_trending.py` ne bloque plus si
  `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` sont absents : il logue une
  info sur stderr et continue en mode YouTube uniquement, au lieu de
  `sys.exit(1)`. README mis à jour (note dans la section find_trending.py
  et dans "Limites à connaître").
- **Rollback:** Dans `find_trending.py`, remplacer le bloc :
  ```python
  if not youtube_key:
      print("Erreur : aucune clé API YouTube trouvée. Définissez YOUTUBE_API_KEY ou utilisez --youtube-key.", file=sys.stderr)
      sys.exit(1)

  subreddits = [s.strip() for s in args.subreddits.split(",") if s.strip()]

  try:
      youtube_results = fetch_youtube_trending(
          youtube_key, args.youtube_region, args.youtube_category, args.youtube_max, args.min_comments
      )
  except RuntimeError as e:
      print(f"Erreur : {e}", file=sys.stderr)
      sys.exit(1)

  reddit_results = []
  if reddit_client_id and reddit_client_secret:
      try:
          reddit_results = fetch_reddit_trending(
              reddit_client_id, reddit_client_secret, subreddits, args.reddit_limit, args.min_comments
          )
      except RuntimeError as e:
          print(f"Erreur : {e}", file=sys.stderr)
          sys.exit(1)
  else:
      print("Info : identifiants Reddit absents (accès API Reddit fermé en self-service), recherche limitée à YouTube.", file=sys.stderr)
  ```
  par :
  ```python
  if not youtube_key:
      print("Erreur : aucune clé API YouTube trouvée. Définissez YOUTUBE_API_KEY ou utilisez --youtube-key.", file=sys.stderr)
      sys.exit(1)
  if not reddit_client_id or not reddit_client_secret:
      print("Erreur : identifiants Reddit manquants. Définissez REDDIT_CLIENT_ID et REDDIT_CLIENT_SECRET, ou utilisez --reddit-client-id/--reddit-client-secret.", file=sys.stderr)
      sys.exit(1)

  subreddits = [s.strip() for s in args.subreddits.split(",") if s.strip()]

  try:
      youtube_results = fetch_youtube_trending(
          youtube_key, args.youtube_region, args.youtube_category, args.youtube_max, args.min_comments
      )
  except RuntimeError as e:
      print(f"Erreur : {e}", file=sys.stderr)
      sys.exit(1)

  try:
      reddit_results = fetch_reddit_trending(
          reddit_client_id, reddit_client_secret, subreddits, args.reddit_limit, args.min_comments
      )
  except RuntimeError as e:
      print(f"Erreur : {e}", file=sys.stderr)
      sys.exit(1)
  ```
  Dans README.md, retirer le paragraphe "⚠️ Reddit a fermé l'accès
  self-service..." de la section find_trending.py, et retirer le point
  "**Reddit a fermé l'inscription self-service...**" de "Limites à connaître".

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
