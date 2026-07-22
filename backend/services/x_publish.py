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
    """Generative Stream: <wire pack>. #StyleCamel

    This reply is the real news payload — main caption is mood/art only.
    Fill up to 280 with primary + secondary headlines when stream_slug is short.
    """
    meta = meta or {}
    style_tag = style_hashtag(meta)
    prefix = "Generative Stream: "
    suffix = f" #{style_tag}"
    budget = _TWEET_MAX - len(prefix) - len(suffix)

    slug = (meta.get("stream_slug") or "").strip()
    slug = re.sub(r"#\w+", "", slug).strip()

    # Prefer full wire pack at publish time — stream_slug may be an older short draft
    try:
        from services.xai_chat import pack_stream_slug

        titles: list[str] = []
        for line in (meta.get("events") or "").splitlines():
            line = line.strip().lstrip("-• ").strip()
            if not line:
                continue
            titles.append(line.split(" — ")[0].strip())
        if titles:
            packed = pack_stream_slug(titles, max_chars=budget)
            # Use packed when missing, short, or clearly denser with secondaries
            if not slug or len(packed) > len(slug) + 15 or " · " in packed and " · " not in slug:
                slug = packed
    except Exception:
        pass

    if not slug:
        slug = "One live story from the wire."

    if len(slug) > budget:
        slug = slug[: budget - 1].rsplit(" ", 1)[0].rstrip(",;:·-–—") + "…"
    # single-line period only when not a multi-headline pack
    if " · " not in slug and slug and slug[-1] not in ".!?…":
        if len(slug) + 1 <= budget:
            slug = slug + "."

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
    """Upload media + create main tweet. Retries on 403 with unique caption variants."""
    media = api_v1.media_upload(img_path)
    media_id = media.media_id
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

    last_err: BaseException | None = None
    for i, text in enumerate(candidates):
        try:
            if i:
                time.sleep(1.5 * i)
            root = client.create_tweet(
                text=text,
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


def publish_run(run_id: str, with_comments: bool = True) -> dict[str, Any]:
    """Upload art.png, tweet caption, one Generative Stream reply."""
    meta = art_store.load_run(run_id)
    if not meta:
        raise FileNotFoundError(f"run not found: {run_id}")
    if meta.get("status") != "complete":
        raise RuntimeError(f"run not complete: {meta.get('status')}")

    img = art_store.image_path(run_id)
    if not img.is_file():
        raise FileNotFoundError(f"image missing: {img}")

    caption = (meta.get("caption") or "").strip()
    if not caption:
        raise RuntimeError("run has no caption")

    if meta.get("x_post_id") and not meta.get("x_force_repost"):
        return {
            "ok": True,
            "already_posted": True,
            "run_id": run_id,
            "x_post_id": meta.get("x_post_id"),
            "x_url": meta.get("x_url"),
            "handle": settings.X_ACCOUNT_HANDLE,
            "replies": meta.get("x_replies") or [],
            "reply_count": sum(1 for r in (meta.get("x_replies") or []) if r.get("ok")),
        }

    api_v1, client = _client_pair()
    post_id, x_url = _create_main_tweet(client, api_v1, str(img), caption, meta)

    # Persist main post immediately so a reply failure still leaves a URL
    meta["x_post_id"] = post_id
    meta["x_url"] = x_url
    meta["x_handle"] = settings.X_ACCOUNT_HANDLE
    meta["x_posted_at"] = datetime.now(timezone.utc).isoformat()
    meta["x_caption_posted"] = _normalize_caption(caption, meta)
    art_store.save_run(meta)

    replies: list[dict[str, Any]] = []
    if with_comments:
        replies.append(_post_stream_reply(client, meta, post_id))
        meta["x_replies"] = replies
        art_store.save_run(meta)

    reply_ok = sum(1 for r in replies if r.get("ok"))
    return {
        "ok": True,
        "already_posted": False,
        "run_id": run_id,
        "x_post_id": post_id,
        "x_url": x_url,
        "handle": settings.X_ACCOUNT_HANDLE,
        "caption": meta.get("x_caption_posted") or caption,
        "replies": replies,
        "reply_count": reply_ok,
        "reply_failed": reply_ok == 0 and with_comments,
    }


def reply_to_existing(run_id: str) -> dict[str, Any]:
    """Attach Generative Stream reply to an already-posted main tweet (repair path)."""
    meta = art_store.load_run(run_id)
    if not meta:
        raise FileNotFoundError(f"run not found: {run_id}")
    post_id = meta.get("x_post_id")
    if not post_id:
        raise RuntimeError("run has no x_post_id — post the main image first")

    for r in meta.get("x_replies") or []:
        if r.get("ok") and r.get("kind") == "generative_stream":
            return {
                "ok": True,
                "already_replied": True,
                "run_id": run_id,
                "replies": meta.get("x_replies"),
                "x_url": meta.get("x_url"),
            }

    _, client = _client_pair()
    result = _post_stream_reply(client, meta, str(post_id))
    replies = list(meta.get("x_replies") or [])
    replies.append(result)
    meta["x_replies"] = replies
    meta["updated_at"] = datetime.now(timezone.utc).isoformat()
    art_store.save_run(meta)
    return {
        "ok": bool(result.get("ok")),
        "already_replied": False,
        "run_id": run_id,
        "reply": result,
        "x_url": meta.get("x_url"),
    }


def preview_post(run_id: str) -> dict[str, Any]:
    meta = art_store.load_run(run_id)
    if not meta:
        raise FileNotFoundError(f"run not found: {run_id}")
    caption = (meta.get("caption") or "").strip()
    comments = build_comment_thread(meta)
    posted = _normalize_caption(caption, meta)
    return {
        "run_id": run_id,
        "handle": settings.X_ACCOUNT_HANDLE,
        "credentials_ready": x_credentials_ready(),
        "has_image": art_store.image_path(run_id).is_file(),
        "already_posted": bool(meta.get("x_post_id")),
        "x_url": meta.get("x_url"),
        "main_post": posted,
        "main_chars": len(posted),
        "comments": comments,
        "comment_count": len(comments),
        "stream_slug": meta.get("stream_slug"),
        "events_source": meta.get("events_source"),
        "limits": {
            "chars_per_tweet": _TWEET_MAX,
            "note": "Main: caption + #PlanetHack #StyleCamel. Reply: Generative Stream slug.",
        },
    }
