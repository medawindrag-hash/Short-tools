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
