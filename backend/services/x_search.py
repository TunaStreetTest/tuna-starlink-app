"""X recent search for Planet Hack news lanes (Session 2)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from config import settings

log = logging.getLogger("tuna-starlink.x_search")

# Lane → recent-search query (English, no retweets). Keep simple for Free/Basic tiers.
_LANE_QUERIES: dict[str, str] = {
    "geopolitics": (
        "(war OR ceasefire OR sanctions OR diplomacy OR election OR treaty OR NATO OR UN) "
        "-is:retweet -is:reply lang:en"
    ),
    "tech": (
        "(AI OR artificial intelligence OR chip OR semiconductor OR cyber OR hack OR GPU OR launch) "
        "-is:retweet -is:reply lang:en"
    ),
    "science": (
        "(NASA OR space OR climate OR energy OR fusion OR quantum OR research OR storm OR wildfire) "
        "-is:retweet -is:reply lang:en"
    ),
    "markets": (
        "(markets OR stocks OR tariff OR Fed OR inflation OR bank OR trade OR protest OR strike) "
        "-is:retweet -is:reply lang:en"
    ),
}


def _client():
    import tweepy

    if not all(
        [
            settings.X_API_KEY,
            settings.X_API_SECRET,
            settings.X_ACCESS_TOKEN,
            settings.X_ACCESS_TOKEN_SECRET,
        ]
    ):
        raise RuntimeError("X credentials incomplete for search")
    return tweepy.Client(
        consumer_key=settings.X_API_KEY,
        consumer_secret=settings.X_API_SECRET,
        access_token=settings.X_ACCESS_TOKEN,
        access_token_secret=settings.X_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=False,
    )


def search_lane(lane: str, max_results: int = 15) -> list[dict[str, Any]]:
    """
    Recent search for a news lane. Returns list of {id, text, metrics, url, score}.
    Empty list on failure / no results (caller falls back to RSS stream).
    """
    lane = (lane or "geopolitics").lower().strip()
    query = _LANE_QUERIES.get(lane) or _LANE_QUERIES["geopolitics"]
    max_results = max(10, min(int(max_results), 20))  # API: 10–100 for recent search

    try:
        client = _client()
        resp = client.search_recent_tweets(
            query=query,
            max_results=max_results,
            tweet_fields=["public_metrics", "created_at", "lang"],
            user_auth=True,
        )
    except Exception as e:
        log.warning("X search failed lane=%s: %s", lane, e)
        return []

    data = getattr(resp, "data", None) or []
    out: list[dict[str, Any]] = []
    for tw in data:
        metrics = getattr(tw, "public_metrics", None) or {}
        if isinstance(metrics, dict):
            likes = int(metrics.get("like_count") or 0)
            rts = int(metrics.get("retweet_count") or 0)
            replies = int(metrics.get("reply_count") or 0)
            quotes = int(metrics.get("quote_count") or 0)
        else:
            likes = rts = replies = quotes = 0
        # Engagement score — prefer viral over empty
        score = likes + 2 * rts + quotes + replies
        text = (getattr(tw, "text", None) or "").replace("\n", " ").strip()
        if len(text) < 20:
            continue
        tid = str(getattr(tw, "id", "") or "")
        out.append(
            {
                "id": tid,
                "text": text,
                "line": text[:200],
                "score": score,
                "likes": likes,
                "retweets": rts,
                "url": f"https://x.com/i/web/status/{tid}" if tid else "",
                "lane": lane,
                "source": "x-search",
                "created_at": str(getattr(tw, "created_at", "") or ""),
            }
        )

    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def pick_best_story(lane: str) -> dict[str, Any] | None:
    """Single best story for this lane, or None."""
    hits = search_lane(lane, max_results=15)
    if not hits:
        return None
    # Prefer some engagement if any post has it; else take top text
    engaged = [h for h in hits if h["score"] >= 5]
    pool = engaged or hits
    best = pool[0]
    return best
