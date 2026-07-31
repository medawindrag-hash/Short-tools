#!/usr/bin/env python3
"""
get_comments.py — Récupère et classe les commentaires les plus populaires
d'une vidéo YouTube via l'API officielle YouTube Data API v3.

Usage :
    python get_comments.py <URL_ou_ID_video> [--top 20] [--min-likes 5] [--out fichier.txt]

Nécessite une clé API YouTube Data v3 (gratuite) définie dans la variable
d'environnement YOUTUBE_API_KEY, ou passée avec --key.

Voir README.md pour la marche à suivre.
"""

import argparse
import os
import re
import sys
import json
import urllib.request
import urllib.parse
import urllib.error

API_BASE = "https://www.googleapis.com/youtube/v3/commentThreads"


def extract_video_id(url_or_id: str) -> str:
    """Accepte une URL YouTube complète, une URL courte, ou un ID brut."""
    url_or_id = url_or_id.strip()

    # Déjà un ID brut (11 caractères typiques, sans slash ni point)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id

    patterns = [
        r"(?:v=|/videos/|embed/|youtu\.be/|/shorts/|/live/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    raise ValueError(f"Impossible d'extraire l'ID vidéo depuis : {url_or_id}")


def fetch_comments(video_id: str, api_key: str, max_total: int = 300):
    """Récupère les commentaires (top-level) via pagination, triés par pertinence."""
    comments = []
    page_token = None

    while len(comments) < max_total:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": api_key,
            "maxResults": 100,
            "order": "relevance",  # YouTube pré-trie déjà par popularité/pertinence
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token

        url = f"{API_BASE}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Erreur API ({e.code}) : {body}") from e

        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": snippet.get("authorDisplayName", "?"),
                "text": snippet.get("textDisplay", "").strip(),
                "likes": snippet.get("likeCount", 0),
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return comments


def main():
    parser = argparse.ArgumentParser(description="Récupère les commentaires les plus populaires d'une vidéo YouTube.")
    parser.add_argument("video", help="URL ou ID de la vidéo YouTube")
    parser.add_argument("--top", type=int, default=20, help="Nombre de commentaires à garder (défaut : 20)")
    parser.add_argument("--min-likes", type=int, default=0, help="Filtre : likes minimum (défaut : 0)")
    parser.add_argument("--key", default=None, help="Clé API YouTube (sinon lue depuis YOUTUBE_API_KEY)")
    parser.add_argument("--out", default=None, help="Fichier de sortie .txt (sinon affichage terminal uniquement)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Format de sortie : texte lisible ou JSON structuré pour chaînage avec d'autres scripts (défaut : text)")
    args = parser.parse_args()

    api_key = args.key or os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("Erreur : aucune clé API trouvée. Définissez YOUTUBE_API_KEY ou utilisez --key.", file=sys.stderr)
        print("Voir README.md pour obtenir une clé gratuite.", file=sys.stderr)
        sys.exit(1)

    try:
        video_id = extract_video_id(args.video)
    except ValueError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    try:
        comments = fetch_comments(video_id, api_key)
    except RuntimeError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    # Filtre + tri par likes décroissants
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
