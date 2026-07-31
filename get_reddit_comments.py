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
