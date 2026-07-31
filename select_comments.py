#!/usr/bin/env python3
"""
select_comments.py — Sélectionne et calibre les commentaires les plus adaptés
à un short chanté d'une durée cible, à partir de la sortie JSON de
get_comments.py.

Usage :
    python get_comments.py <video> --format json --out comments.json
    python select_comments.py comments.json --target-duration 55 --out selection.json

Ou en pipe :
    python get_comments.py <video> --format json | python select_comments.py - --target-duration 55

Filtre le spam (liens, uniquement des emojis, commentaires trop courts),
déduplique, puis retient les commentaires les mieux likés jusqu'à épuiser
un budget de durée estimée (mots / débit de chant en mots-par-minute).

Voir README.md pour le détail du pipeline.
"""

import argparse
import json
import re
import sys

URL_RE = re.compile(r"https?://\S+")
EMOJI_ONLY_RE = re.compile(
    r"^[\s\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]+$"
)


def load_comments(source: str):
    if source == "-":
        raw = sys.stdin.read()
    else:
        with open(source, "r", encoding="utf-8") as f:
            raw = f.read()
    return json.loads(raw)


def is_spam(text: str, min_words: int) -> bool:
    """Filtre grossier : liens, emojis seuls, ou trop peu de mots."""
    stripped = text.strip()
    if not stripped:
        return True
    if URL_RE.search(stripped):
        return True
    if EMOJI_ONLY_RE.match(stripped):
        return True
    if len(stripped.split()) < min_words:
        return True
    return False


def dedupe(comments):
    seen = set()
    result = []
    for c in comments:
        key = c["text"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(c)
    return result


def estimate_duration(text: str, words_per_minute: float) -> float:
    word_count = len(text.split())
    return round((word_count / words_per_minute) * 60, 2)


def main():
    parser = argparse.ArgumentParser(
        description="Sélectionne les commentaires les plus adaptés à un short chanté, dans un budget de durée donné."
    )
    parser.add_argument("source", help="Fichier JSON produit par get_comments.py --format json (ou '-' pour lire depuis stdin)")
    parser.add_argument("--target-duration", type=float, default=55.0, help="Durée cible en secondes pour l'ensemble des commentaires chantés (défaut : 55)")
    parser.add_argument("--max-segments", type=int, default=None, help="Nombre maximum de commentaires à retenir (défaut : illimité, contraint seulement par la durée)")
    parser.add_argument("--min-words", type=int, default=4, help="Nombre de mots minimum pour qu'un commentaire soit retenu, filtre anti-spam (défaut : 4)")
    parser.add_argument("--max-chars", type=int, default=220, help="Nombre de caractères maximum par commentaire retenu (défaut : 220)")
    parser.add_argument("--wpm", type=float, default=90.0, help="Débit estimé du chant/lecture en mots par minute, pour estimer la durée de chaque commentaire (défaut : 90)")
    parser.add_argument("--out", default=None, help="Fichier de sortie .json (sinon affichage terminal uniquement)")
    args = parser.parse_args()

    comments = load_comments(args.source)

    filtered = [
        c for c in comments
        if not is_spam(c["text"], args.min_words) and len(c["text"]) <= args.max_chars
    ]
    filtered = dedupe(filtered)
    filtered.sort(key=lambda c: c["likes"], reverse=True)

    selected = []
    cumulative = 0.0
    for c in filtered:
        if args.max_segments is not None and len(selected) >= args.max_segments:
            break
        duration = estimate_duration(c["text"], args.wpm)
        if cumulative + duration > args.target_duration and selected:
            continue
        cumulative += duration
        selected.append({
            "order": len(selected) + 1,
            "author": c["author"],
            "text": c["text"],
            "likes": c["likes"],
            "word_count": len(c["text"].split()),
            "est_duration_sec": duration,
            "cumulative_duration_sec": round(cumulative, 2),
        })
        if cumulative >= args.target_duration:
            break

    if not selected:
        print("Aucun commentaire retenu avec ces critères.", file=sys.stderr)
        sys.exit(1)

    output = json.dumps(selected, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"{len(selected)} commentaires retenus (~{cumulative:.1f}s estimées) écrits dans {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
