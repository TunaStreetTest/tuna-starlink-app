"""X (Twitter) publish for Planet Hack — media post + one news-context reply.

Main post: image + caption (#PlanetHack).
One reply: headlines/keywords that fueled the piece (discovery).
"""

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


def _normalize_caption(caption: str, run_id: str = "") -> str:
    """Single-line caption, under 280, unique enough to avoid X 403 duplicates."""
    # Collapse newlines / weird whitespace (Grok sometimes does "…\n#PlanetHack")
    text = re.sub(r"\s+", " ", (caption or "").strip())
    # Ensure hashtag once at end
    text = re.sub(r"(#PlanetHack\s*)+$", "", text, flags=re.I).strip()
    tag = f" · {run_id[-6:]}" if run_id else ""
    suffix = f" #PlanetHack{tag}"
    body_limit = _TWEET_MAX - len(suffix)
    if len(text) > body_limit:
        text = text[: body_limit - 1].rsplit(" ", 1)[0] + "…"
    return (text + suffix).strip()


def _headline_bits(events: str, max_items: int = 6) -> list[str]:
    bits: list[str] = []
    for raw in (events or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-•*]\s*", "", line)
        if line.lower().startswith("dry-run"):
            continue
        title = re.split(r"\s+[—–-]\s+", line, maxsplit=1)[0].strip()
        title = re.sub(r"\s+", " ", title)
        if len(title) < 8:
            continue
        if len(title) > 72:
            title = title[:71].rsplit(" ", 1)[0] + "…"
        if title not in bits:
            bits.append(title)
        if len(bits) >= max_items:
            break
    return bits


def build_news_comment(meta: dict[str, Any] | None = None, *, unique_tag: str = "") -> str:
    meta = meta or {}
    events = (meta.get("events") or "").strip()
    style = (meta.get("style_label") or meta.get("style_id") or "").strip()
    bits = _headline_bits(events)

    tag = ""
    if unique_tag:
        tag = f" · {unique_tag[-8:]}" if len(unique_tag) > 8 else f" · {unique_tag}"

    if not bits:
        return _clip(
            "Planet Hack — painted from today's world wires via Grok + xAI Imagine."
            + (f" [{style}]" if style else "")
            + tag
        )

    prefix = "Wired into this Planet Hack: "
    suffix = (f" · {style}" if style else "") + tag
    budget = _TWEET_MAX - len(prefix) - len(suffix)
    packed: list[str] = []
    used = 0
    for bit in bits:
        sep = 0 if not packed else 3
        if used + sep + len(bit) > budget:
            short = bit[: max(12, budget - used - sep - 1)].rsplit(" ", 1)[0]
            if short and used + sep + len(short) <= budget:
                packed.append(short + "…")
            break
        packed.append(bit)
        used += sep + len(bit)

    body = " · ".join(packed) if packed else bits[0][: max(0, budget)]
    return _clip(prefix + body + suffix)


def build_comment_thread(meta: dict[str, Any]) -> list[dict[str, str]]:
    run_id = (meta.get("run_id") or "")[-6:]
    return [
        {
            "kind": "news_context",
            "text": build_news_comment(meta, unique_tag=run_id),
        }
    ]


def _client_pair():
    import tweepy

    if not x_credentials_ready():
        raise RuntimeError(
            "X credentials incomplete — set X_API_KEY, X_API_SECRET, "
            "X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET"
        )
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
    name = type(err).__name__
    msg = str(err)
    return "403" in msg or "Forbidden" in name or "not permitted" in msg.lower()


def _create_reply(client, text: str, in_reply_to: str) -> str:
    r = client.create_tweet(
        text=text,
        in_reply_to_tweet_id=in_reply_to,
        user_auth=True,
    )
    if not r or not r.data or "id" not in r.data:
        raise RuntimeError(f"empty reply response: {r!r}")
    return str(r.data["id"])


def _post_news_reply(client, meta: dict[str, Any], post_id: str) -> dict[str, Any]:
    handle = settings.X_ACCOUNT_HANDLE.lstrip("@")
    run_id = meta.get("run_id") or ""
    attempts: list[str] = [
        build_news_comment(meta, unique_tag=run_id[-6:]),
        _clip(
            f"Headlines behind this Planet Hack ({run_id[-6:]}): "
            + " · ".join(_headline_bits(meta.get("events") or "", max_items=3))
        ),
        _clip(
            f"Planet Hack source wires · {run_id} · "
            + (meta.get("events") or "today's news").replace("\n", " ")[:160]
        ),
    ]

    last_err = None
    for i, text in enumerate(attempts):
        if not text or len(text) < 5:
            continue
        try:
            time.sleep(2.0 + i * 1.5)
            rid = _create_reply(client, text, post_id)
            return {
                "kind": "news_context",
                "id": rid,
                "url": f"https://x.com/{handle}/status/{rid}",
                "ok": True,
                "text": text,
                "attempt": i + 1,
            }
        except Exception as e:
            last_err = e
            log.warning("X reply attempt %s failed: %s", i + 1, e)
            continue

    return {
        "kind": "news_context",
        "ok": False,
        "error": f"{type(last_err).__name__}: {last_err}" if last_err else "unknown",
    }


def _create_main_tweet(client, api_v1, img_path: str, caption: str, run_id: str) -> tuple[str, str]:
    """Upload media + create main tweet. Retries on 403 with unique caption variants."""
    media = api_v1.media_upload(img_path)
    media_id = media.media_id

    candidates = [
        _normalize_caption(caption, run_id),
        _normalize_caption(caption, run_id + "-b"),
        _clip(
            f"Planet Hack · {run_id} · Grok + xAI Imagine · "
            f"{(caption or '')[:120].replace(chr(10), ' ')} #PlanetHack"
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
            if not _is_forbidden(e) and i == 0:
                # Non-403 on first try — still retry once with unique text
                continue
            continue

    raise RuntimeError(
        f"X main post failed after retries: {type(last_err).__name__}: {last_err}. "
        "Often rate-limit, duplicate, or Free-tier write cap — wait a few minutes and retry."
    )


def publish_run(run_id: str, with_comments: bool = True) -> dict[str, Any]:
    """Upload art.png, tweet caption, one news-context reply (retried)."""
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
        }

    api_v1, client = _client_pair()
    post_id, x_url = _create_main_tweet(
        client, api_v1, str(img), caption, run_id
    )

    # Persist main post immediately so a reply failure still leaves a URL
    meta["x_post_id"] = post_id
    meta["x_url"] = x_url
    meta["x_handle"] = settings.X_ACCOUNT_HANDLE
    meta["x_posted_at"] = datetime.now(timezone.utc).isoformat()
    meta["x_caption_posted"] = _normalize_caption(caption, run_id)
    art_store.save_run(meta)

    replies: list[dict[str, Any]] = []
    if with_comments:
        replies.append(_post_news_reply(client, meta, post_id))
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
    """Attach the news comment to an already-posted main tweet (repair path)."""
    meta = art_store.load_run(run_id)
    if not meta:
        raise FileNotFoundError(f"run not found: {run_id}")
    post_id = meta.get("x_post_id")
    if not post_id:
        raise RuntimeError("run has no x_post_id — post the main image first")

    for r in meta.get("x_replies") or []:
        if r.get("ok") and r.get("kind") == "news_context":
            return {
                "ok": True,
                "already_replied": True,
                "run_id": run_id,
                "replies": meta.get("x_replies"),
                "x_url": meta.get("x_url"),
            }

    _, client = _client_pair()
    result = _post_news_reply(client, meta, str(post_id))
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
    posted = _normalize_caption(caption, meta.get("run_id") or "")
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
        "limits": {
            "chars_per_tweet": _TWEET_MAX,
            "note": "Caption sanitized to one line ≤280; reply is news keywords.",
        },
    }
