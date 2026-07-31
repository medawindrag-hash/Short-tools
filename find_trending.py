#!/usr/bin/env python3
"""
find_trending.py — Repère chaque jour les vidéos YouTube tendance, comme
candidats sources pour get_comments.py.

Usage :
    python find_trending.py --out trending.json

Nécessite le même identifiant que get_comments.py : YOUTUBE_API_KEY
(variable d'environnement, ou passée en option). Voir README.md.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3/videos"


def fetch_youtube_trending(api_key: str, region: str, category: str, max_results: int, min_comments: int) -> list:
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": min(max_results, 50),
        "key": api_key,
    }
    if category:
        params["videoCategoryId"] = category

    url = f"{YOUTUBE_API_BASE}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Erreur API YouTube ({e.code}) : {body}") from e

    return parse_youtube_trending(data, min_comments)


def parse_youtube_trending(data, min_comments: int) -> list:
    """Extrait et filtre les candidats depuis la réponse JSON de videos.list.

    Séparé de fetch_youtube_trending pour être testable sans appel réseau.
    """
    results = []
    for item in data.get("items", []):
        stats = item.get("statistics", {})
        comment_count = int(stats.get("commentCount", 0))
        if comment_count < min_comments:
            continue
        results.append({
            "source": "youtube",
            "id": item["id"],
            "title": item["snippet"]["title"],
            "url": f"https://youtu.be/{item['id']}",
            "comment_count": comment_count,
            "view_count": int(stats.get("viewCount", 0)),
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Repère les vidéos YouTube tendance du jour, comme candidats sources pour la suite du pipeline.")
    parser.add_argument("--youtube-region", default="US", help="Code région YouTube pour les tendances (défaut : US)")
    parser.add_argument("--youtube-category", default=None, help="ID de catégorie YouTube à filtrer (ex : 23 = Comedy, 24 = Entertainment). Défaut : aucun filtre")
    parser.add_argument("--youtube-max", type=int, default=25, help="Nombre max de vidéos YouTube à considérer (défaut : 25, max 50)")
    parser.add_argument("--min-comments", type=int, default=50, help="Nombre de commentaires minimum pour qu'une vidéo soit retenue (défaut : 50)")
    parser.add_argument("--top", type=int, default=20, help="Nombre total de candidats à garder, triés par nombre de commentaires (défaut : 20)")
    parser.add_argument("--youtube-key", default=None, help="Clé API YouTube (sinon lue depuis YOUTUBE_API_KEY)")
    parser.add_argument("--out", default=None, help="Fichier de sortie .json (sinon affichage terminal uniquement)")
    args = parser.parse_args()

    youtube_key = args.youtube_key or os.environ.get("YOUTUBE_API_KEY")

    if not youtube_key:
        print("Erreur : aucune clé API YouTube trouvée. Définissez YOUTUBE_API_KEY ou utilisez --youtube-key.", file=sys.stderr)
        sys.exit(1)

    try:
        combined = fetch_youtube_trending(
            youtube_key, args.youtube_region, args.youtube_category, args.youtube_max, args.min_comments
        )
    except RuntimeError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    combined.sort(key=lambda r: r["comment_count"], reverse=True)
    combined = combined[: args.top]

    if not combined:
        print("Aucun candidat trouvé avec ces critères.")
        return

    output = json.dumps(combined, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"{len(combined)} candidats écrits dans {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
