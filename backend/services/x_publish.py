"""X publish — main caption + #PlanetHack #StyleCamel; reply Generative Stream."""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone
from typing import Any

from config import settings
from services import art_store

log = logging.getLogger("tuna-starlink.x_publish")
_TWEET_MAX = 280


def x_credentials_ready() -> bool:
    return all(
        [
            settings.X_API_KEY,
            settings.X_API_SECRET,
            settings.X_ACCESS_TOKEN,
            settings.X_ACCESS_TOKEN_SECRET,
        ]
    )


def _clip(text: str, limit: int = _TWEET_MAX) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def style_hashtag(meta: dict[str, Any] | None) -> str:
    meta = meta or {}
    tag = (meta.get("style_hashtag") or "").strip().lstrip("#")
    if tag:
        return tag
    label = (meta.get("style_label") or meta.get("style_id") or "PlanetHack").strip()
    parts = re.split(r"[\s_\-]+", label)
    return "".join(p[:1].upper() + p[1:] for p in parts if p) or "PlanetHack"


def _normalize_caption(caption: str, meta: dict[str, Any] | None = None) -> str:
    """Body + #PlanetHack #StyleCamel (no run-id salt)."""
    text = re.sub(r"\s+", " ", (caption or "").strip())
    text = re.sub(r"#\w+", "", text).strip()  # strip any model hashtags
    style_tag = style_hashtag(meta)
    suffix = f" #PlanetHack #{style_tag}"
    body_limit = _TWEET_MAX - len(suffix)
    if len(text) > body_limit:
        text = text[: body_limit - 1].rsplit(" ", 1)[0] + "…"
    return (text + suffix).strip()


def build_generative_stream_reply(meta: dict[str, Any] | None = None) -> str:
    """Generative Stream: <slug>. #StyleCamel  — no #PlanetHack in reply."""
    meta = meta or {}
    style_tag = style_hashtag(meta)
    slug = (meta.get("stream_slug") or "").strip()
    if not slug:
        # fallback from events first line
        events = meta.get("events") or ""
        for line in events.splitlines():
            line = line.strip().lstrip("-• ").strip()
            if line:
                slug = line.split(" — ")[0].strip()[:160]
                break
        if not slug:
            slug = "One live story from the wire"
    slug = re.sub(r"#\w+", "", slug).strip()
    # ensure ends with period for readability
    if slug and slug[-1] not in ".!?":
        slug = slug + "."
    prefix = "Generative Stream: "
    suffix = f" #{style_tag}"
    budget = _TWEET_MAX - len(prefix) - len(suffix)
    if len(slug) > budget:
        slug = slug[: budget - 1].rsplit(" ", 1)[0] + "…"
    return _clip(prefix + slug + suffix)


def build_comment_thread(meta: dict[str, Any]) -> list[dict[str, str]]:
    return [{"kind": "generative_stream", "text": build_generative_stream_reply(meta)}]


def _client_pair():
    import tweepy

    if not x_credentials_ready():
        raise RuntimeError("X credentials incomplete")
    auth = tweepy.OAuth1UserHandler(
        settings.X_API_KEY,
        settings.X_API_SECRET,
        settings.X_ACCESS_TOKEN,
        settings.X_ACCESS_TOKEN_SECRET,
    )
    api_v1 = tweepy.API(auth)
    client = tweepy.Client(
        consumer_key=settings.X_API_KEY,
        consumer_secret=settings.X_API_SECRET,
        access_token=settings.X_ACCESS_TOKEN,
        access_token_secret=settings.X_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True,
    )
    return api_v1, client


def _is_forbidden(err: BaseException) -> bool:
    msg = str(err)
    return "403" in msg or "Forbidden" in type(err).__name__ or "not permitted" in msg.lower()


def _create_reply(client, text: str, in_reply_to: str) -> str:
    r = client.create_tweet(
        text=text, in_reply_to_tweet_id=in_reply_to, user_auth=True
    )
    if not r or not r.data or "id" not in r.data:
        raise RuntimeError(f"empty reply response: {r!r}")
    return str(r.data["id"])


def _post_stream_reply(client, meta: dict[str, Any], post_id: str) -> dict[str, Any]:
    handle = settings.X_ACCOUNT_HANDLE.lstrip("@")
    text = build_generative_stream_reply(meta)
    attempts = [
        text,
        _clip(
            f"Generative Stream: {(meta.get('events') or 'live wire')[:120].split(chr(10))[0].lstrip('- ')}. "
            f"#{style_hashtag(meta)}"
        ),
    ]
    last_err = None
    for i, body in enumerate(attempts):
        try:
            time.sleep(2.0 + i * 1.5)
            rid = _create_reply(client, body, post_id)
            return {
                "kind": "generative_stream",
                "id": rid,
                "url": f"https://x.com/{handle}/status/{rid}",
                "ok": True,
                "text": body,
                "attempt": i + 1,
            }
        except Exception as e:
            last_err = e
            log.warning("X reply attempt %s failed: %s", i + 1, e)
    return {
        "kind": "generative_stream",
        "ok": False,
        "error": f"{type(last_err).__name__}: {last_err}" if last_err else "unknown",
    }


def _create_main_tweet(
    client, api_v1, img_path: str, caption: str, meta: dict[str, Any]
) -> tuple[str, str]:
    media = api_v1.media_upload(img_path)
    media_id = media.media_id
    run_id = meta.get("run_id") or ""
    base = _normalize_caption(caption, meta)
    # unique retry variants without ugly salts when possible
    candidates = [
        base,
        _normalize_caption(caption + " ·", meta),
        _clip(
            re.sub(r"#\w+", "", caption or "")[:100].strip()
            + f" — Planet Hack. #PlanetHack #{style_hashtag(meta)}"
        ),
    ]
