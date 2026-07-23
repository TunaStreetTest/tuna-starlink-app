"""X publish — image + single-headline Generative Stream body (no hashtags, no reply)."""

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
    cut = text[: max(limit - 1, 1)].rsplit(" ", 1)[0].rstrip(",;:·-–—")
    if not cut:
        cut = text[: max(limit - 1, 1)]
    return cut + "…"


def build_main_post(meta: dict[str, Any] | None = None) -> str:
    """Main X body: Generative Stream text, full 280 budget, no hashtags."""
    meta = meta or {}
    from services.xai_chat import _clean_headline_piece

    # Prefer stream_slug (already filled toward 280 at generate time)
    body = (meta.get("stream_slug") or meta.get("caption") or "").strip()
    if not body:
        for line in (meta.get("events") or "").splitlines():
            line = line.strip().lstrip("-• ").strip()
            if line:
                body = line
                break
    body = _clean_headline_piece(body)
    body = re.sub(r"#\w+", "", body)
    body = re.sub(r"https?://\S+", "", body)
    body = re.sub(r"@\w+", "", body)
    body = re.sub(r"\s+", " ", body).strip()
    if not body:
        body = "A live story from the wire."
    body = _clip(body, _TWEET_MAX)
    if body and body[-1] not in ".!?…":
        if len(body) + 1 <= _TWEET_MAX:
            body = body + "."
        else:
            body = _clip(body, _TWEET_MAX - 1) + "."
    return body


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


def _create_main_tweet(
    client, api_v1, img_path: str, text: str
) -> tuple[str, str]:
    """Upload media + create main tweet. Retries on 403 with slight variants."""
    media = api_v1.media_upload(img_path)
    media_id = media.media_id
    base = _clip(re.sub(r"#\w+", "", text or "").strip(), _TWEET_MAX)
    candidates = [
        base,
        _clip(base.rstrip(".!") + " ·", _TWEET_MAX) if base else base,
        _clip((base[:200] + " — live wire.") if base else "Live wire.", _TWEET_MAX),
    ]

    last_err: BaseException | None = None
    for i, body in enumerate(candidates):
        try:
            if i:
                time.sleep(1.5 * i)
            root = client.create_tweet(
                text=body,
                media_ids=[media_id],
                user_auth=True,
            )
            post_id = str(root.data["id"])
            handle = settings.X_ACCOUNT_HANDLE.lstrip("@")
            return post_id, f"https://x.com/{handle}/status/{post_id}"
        except Exception as e:
            last_err = e
            log.warning("X main tweet attempt %s failed: %s", i + 1, e)
            continue

    raise RuntimeError(
        f"X main post failed after retries: {type(last_err).__name__}: {last_err}. "
        "Often rate-limit, duplicate, or Free-tier write cap — wait a few minutes and retry."
    )


def publish_run(run_id: str, with_comments: bool = False) -> dict[str, Any]:
    """Upload art.png + single-headline Generative Stream body. No reply by default."""
    meta = art_store.load_run(run_id)
    if not meta:
        raise FileNotFoundError(f"run not found: {run_id}")
    if meta.get("status") != "complete":
        raise RuntimeError(f"run not complete: {meta.get('status')}")

    img = art_store.image_path(run_id)
    if not img.is_file():
        raise FileNotFoundError(f"image missing: {img}")

    post_text = build_main_post(meta)
    if not post_text:
        raise RuntimeError("run has no Generative Stream headline")

    if meta.get("x_post_id") and not meta.get("x_force_repost"):
        return {
            "ok": True,
            "already_posted": True,
            "run_id": run_id,
            "x_post_id": meta.get("x_post_id"),
            "x_url": meta.get("x_url"),
            "handle": settings.X_ACCOUNT_HANDLE,
            "post_text": meta.get("x_caption_posted") or post_text,
            "replies": [],
            "reply_count": 0,
        }

    api_v1, client = _client_pair()
    post_id, x_url = _create_main_tweet(client, api_v1, str(img), post_text)

    meta["x_post_id"] = post_id
    meta["x_url"] = x_url
    meta["x_handle"] = settings.X_ACCOUNT_HANDLE
    meta["x_posted_at"] = datetime.now(timezone.utc).isoformat()
    meta["x_caption_posted"] = post_text
    meta["x_replies"] = []
    art_store.save_run(meta)

    return {
        "ok": True,
        "already_posted": False,
        "run_id": run_id,
        "x_post_id": post_id,
        "x_url": x_url,
        "handle": settings.X_ACCOUNT_HANDLE,
        "caption": post_text,  # API compat
        "post_text": post_text,
        "replies": [],
        "reply_count": 0,
        "reply_failed": False,
    }


def reply_to_existing(run_id: str) -> dict[str, Any]:
    """No-op: single-post contract (no Generative Stream reply)."""
    meta = art_store.load_run(run_id)
    if not meta:
        raise FileNotFoundError(f"run not found: {run_id}")
    return {
        "ok": True,
        "skipped": True,
        "note": "replies disabled — main post is the Generative Stream headline",
        "run_id": run_id,
        "x_url": meta.get("x_url"),
    }


def preview_post(run_id: str) -> dict[str, Any]:
    meta = art_store.load_run(run_id)
    if not meta:
        raise FileNotFoundError(f"run not found: {run_id}")
    posted = build_main_post(meta)
    return {
        "run_id": run_id,
        "handle": settings.X_ACCOUNT_HANDLE,
        "credentials_ready": x_credentials_ready(),
        "has_image": art_store.image_path(run_id).is_file(),
        "already_posted": bool(meta.get("x_post_id")),
        "x_url": meta.get("x_url"),
        "main_post": posted,
        "main_chars": len(posted),
        "comments": [],
        "comment_count": 0,
        "stream_slug": meta.get("stream_slug"),
        "events_source": meta.get("events_source"),
        "limits": {
            "chars_per_tweet": _TWEET_MAX,
            "note": "Main: single headline Generative Stream, full 280, no hashtags, no reply.",
        },
    }
