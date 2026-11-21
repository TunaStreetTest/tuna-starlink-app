"""X publish — image + Tuna Starlink body (longer form, no hashtags, no reply)."""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings
from services import art_store

log = logging.getLogger("tuna-starlink.x_publish")
_TWEET_MAX = 4000
_PLATE_ORIGIN = "https://planethack.space"
_RUN_ID = re.compile(r"^[A-Za-z0-9_-]+$")


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


def plate_url_for(run_id: str | None) -> str | None:
    """Public glass for one plate. The path is a 7-character code, not the run id."""
    rid = (run_id or "").strip()
    if not _RUN_ID.fullmatch(rid):
        return None
    return f"{_PLATE_ORIGIN}/p/{_export_module().plate_code(rid)}"


def _split_plate(text: str) -> tuple[str, str | None]:
    if "\n" not in text:
        return text, None
    caption, last = text.rsplit("\n", 1)
    if last.startswith(f"{_PLATE_ORIGIN}/p/"):
        return caption, last
    return text, None


def _join_plate(caption: str, url: str, limit: int) -> str:
    """Caption, then the plate URL on its own line. The URL is never clipped."""
    url = url.strip()
    caption = (caption or "").strip()
    if not url:
        return _clip(caption, limit)
    if len(url) > limit:
        return url
    room = limit - len(url) - 1
    if room <= 0 or not caption:
        return url
    clipped = _clip(caption, room)
    if not clipped:
        return url
    return f"{clipped}\n{url}"


def clip_keeping_plate(text: str, limit: int) -> str:
    caption, url = _split_plate(text or "")
    if not url:
        return _clip(text, limit)
    return _join_plate(caption, url, limit)


def tweet_bodies(text: str) -> list[str]:
    """Long body, then a 280-character fallback. Both keep the full plate URL."""
    cleaned = re.sub(r"#\w+", "", text or "").strip()
    base = clip_keeping_plate(cleaned, _TWEET_MAX)
    bodies = [base] if base else []
    if not base:
        return bodies
    if len(base) > 280:
        bodies.append(clip_keeping_plate(base, 280))
        return bodies
    caption, url = _split_plate(base)
    if url:
        variant = _join_plate(caption.rstrip(".!") + " ·", url, 280)
    else:
        variant = _clip(base.rstrip(".!") + " ·", 280)
    if variant and variant != base:
        bodies.append(variant)
    return bodies


def build_main_post(meta: dict[str, Any] | None = None) -> str:
    """Main X body: Tuna Starlink caption, then the plate URL on its own line."""
    meta = meta or {}
    from services.xai_chat import _clean_post_body

    body = (meta.get("caption") or meta.get("stream_slug") or "").strip()
    if not body:
        for line in (meta.get("events") or "").splitlines():
            line = line.strip().lstrip("-• ").strip()
            if line:
                body = line
                break
    if not body:
        body = "A live story from the wire."
    # Cleaner strips URLs and hashtags. The plate link is added after that.
    body = _clean_post_body(body, _TWEET_MAX) or "A live story from the wire."
    url = plate_url_for(str(meta.get("run_id") or ""))
    if not url:
        return body
    return _join_plate(body, url, _TWEET_MAX)


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
    candidates = tweet_bodies(text)

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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _art_root() -> Path:
    art = Path(settings.ART_STORAGE_PATH).expanduser()
    if art.is_absolute():
        return art
    from_backend = (_repo_root() / "backend" / art).resolve()
    if from_backend.is_dir():
        return from_backend
    return (Path.cwd() / art).resolve()


def _export_module():
    path = _repo_root() / "scripts" / "export_public_feed.py"
    spec = importlib.util.spec_from_file_location("export_public_feed", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def export_public_feed() -> dict[str, Any]:
    module = _export_module()
    return module.export_feed(_art_root(), _repo_root() / "public" / "public")


def _sync_site(args: list[str]) -> None:
    script = _repo_root() / "scripts" / "sync-public-site.sh"
    proc = subprocess.run(
        [str(script), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"site sync failed ({' '.join(args)}): {detail}")


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise RuntimeError(f"{url} returned {resp.status}")
            return resp.read()
    except urllib.error.URLError as e:
        raise RuntimeError(f"{url} failed: {e}") from e


def require_plate_on_site(run_id: str) -> None:
    """The jpg is really an image, and feed.json lists this id. Then we may tweet."""
    if not _RUN_ID.fullmatch(run_id):
        raise RuntimeError(f"refusing to check a bad run id: {run_id}")
    jpg = _http_get(f"{_PLATE_ORIGIN}/media/{run_id}.jpg")
    if not jpg.startswith(b"\xff\xd8"):
        raise RuntimeError(f"media/{run_id}.jpg is not a jpeg")
    raw = _http_get(f"{_PLATE_ORIGIN}/feed.json")
    try:
        feed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise RuntimeError(f"feed.json is not json: {e}") from e
    posts = feed.get("posts") if isinstance(feed, dict) else None
    ids = [p.get("id") for p in posts or [] if isinstance(p, dict)]
    if run_id not in ids:
        raise RuntimeError(f"feed.json has no plate {run_id}")


def _push_plate_before_tweet(run_id: str) -> None:
    export_public_feed()
    _sync_site(["plate", run_id])
    require_plate_on_site(run_id)


def _refresh_feed_after_tweet(run_id: str) -> str | None:
    """One more export so the plate's x_url is on the set. No retry loop."""
    try:
        export_public_feed()
        _sync_site(["feed"])
    except Exception as e:
        log.warning("feed refresh after tweet failed run=%s: %s", run_id, e)
        return f"{type(e).__name__}: {e}"
    return None


def publish_run(run_id: str, with_comments: bool = False) -> dict[str, Any]:
    """Put the plate on the site, then upload art.png + the caption and link."""
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
        raise RuntimeError("run has no X caption")

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

    _push_plate_before_tweet(run_id)

    api_v1, client = _client_pair()
    post_id, x_url = _create_main_tweet(client, api_v1, str(img), post_text)

    meta["x_post_id"] = post_id
    meta["x_url"] = x_url
    meta["x_handle"] = settings.X_ACCOUNT_HANDLE
    meta["x_posted_at"] = datetime.now(timezone.utc).isoformat()
    meta["x_caption_posted"] = post_text
    meta["x_replies"] = []
    art_store.save_run(meta)
    feed_refresh_error = _refresh_feed_after_tweet(run_id)

    # Permanent retire — posted wire must never be re-picked on the next generate
    try:
        from services import events as events_svc

        events_svc.mark_run_stories_used(meta, posted=True)
    except Exception as e:
        log.warning("failed to mark posted story used run=%s: %s", run_id, e)

    result = {
        "ok": True,
        "already_posted": False,
        "run_id": run_id,
        "x_post_id": post_id,
        "x_url": x_url,
        "handle": settings.X_ACCOUNT_HANDLE,
        "caption": post_text,  # API compat
        "post_text": post_text,
        "plate_url": plate_url_for(run_id),
        "replies": [],
        "reply_count": 0,
        "reply_failed": False,
    }
    if feed_refresh_error:
        result["feed_refresh_error"] = feed_refresh_error
    return result


def reply_to_existing(run_id: str) -> dict[str, Any]:
    """No-op: single-post contract (no reply)."""
    meta = art_store.load_run(run_id)
    if not meta:
        raise FileNotFoundError(f"run not found: {run_id}")
    return {
        "ok": True,
        "skipped": True,
        "note": "replies disabled — main post is the Tuna Starlink caption",
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
            "note": "Main: Tuna Starlink caption on the image, long-form, no hashtags, no reply.",
        },
    }
