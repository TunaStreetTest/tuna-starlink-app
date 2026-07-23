"""Planet Hack generation pipeline."""

from __future__ import annotations

import asyncio
import traceback
from datetime import datetime, timezone
from typing import Any

from config import settings
from services import art_store, events as events_svc, styles, xai_chat, xai_imagine

_lock = asyncio.Lock()
_current: dict[str, Any] | None = None
_history: list[dict[str, Any]] = []


def pipeline_status() -> dict[str, Any]:
    series = styles.series_info()
    from services import scheduler as sched_svc

    return {
        "current": _current,
        "recent": list(reversed(_history[-20:])),
        "dry_run": settings.DRY_RUN,
        "schedule_enabled": settings.SCHEDULE_ENABLED,
        "schedule_cron": settings.SCHEDULE_CRON or None,
        "schedule_timezone": settings.SCHEDULE_TIMEZONE or None,
        "schedule_interval_minutes": settings.SCHEDULE_INTERVAL_MINUTES,
        "schedule_peak_start_hour": settings.SCHEDULE_PEAK_START_HOUR,
        "schedule_peak_end_hour": settings.SCHEDULE_PEAK_END_HOUR,
        "schedule_max_runs_per_day": settings.SCHEDULE_MAX_RUNS_PER_DAY,
        "schedule_day": sched_svc.schedule_day_stats(),
        "auto_publish": settings.AUTO_PUBLISH,
        "default_style": settings.DEFAULT_STYLE,
        "edge_text": settings.EDGE_TEXT,
        "x_account": settings.X_ACCOUNT_HANDLE,
        "series": series["name"],
        "image_model": settings.XAI_IMAGE_MODEL,
        "chat_model": settings.XAI_CHAT_MODEL,
        "news_stream": events_svc.stream_stats(),
        "x_search_enabled": settings.X_SEARCH_ENABLED,
        "x_search_ttl_minutes": settings.X_SEARCH_TTL_MINUTES,
        "rss_ingest_ttl_minutes": settings.RSS_INGEST_TTL_MINUTES,
    }


def _push_history(meta: dict[str, Any]) -> None:
    _history.append(
        {
            "run_id": meta.get("run_id"),
            "status": meta.get("status"),
            "style": meta.get("style_id"),
            "lane": meta.get("news_lane"),
            "events_source": meta.get("events_source"),
            "updated_at": meta.get("updated_at"),
            "error": meta.get("error"),
            "egress_bytes": meta.get("egress_bytes"),
            "latency_ms": meta.get("latency_ms"),
        }
    )
    if len(_history) > 50:
        del _history[:-50]


async def run_generate(style_id: str | None = None, force: bool = False) -> dict[str, Any]:
    global _current

    async with _lock:
        if _current and _current.get("status") == "running" and not force:
            raise RuntimeError(
                f"generation already running: {_current.get('run_id')} "
                "(pass force=true only if you really mean it)"
            )
        run_id = art_store.new_run_id()
        styles.reload_styles()
        style = styles.get_style(style_id)
        started = datetime.now(timezone.utc)
        meta: dict[str, Any] = {
            "run_id": run_id,
            "status": "running",
            "phase": "events",
            "style_id": style["id"],
            "style_label": style["label"],
            "style_hashtag": style.get("hashtag"),
            "news_lane": style.get("lane"),
            "series": style.get("series_name"),
            "dry_run": settings.DRY_RUN,
            "edge_text": settings.EDGE_TEXT,
            "created_at": started.isoformat(),
            "updated_at": started.isoformat(),
            "events": None,
            "events_source": None,
            "events_tap": None,
            "stream_slug": None,
            "art_brief": None,
            "art_prompt": None,
            "caption": None,
            "egress_bytes": 0,
            "latency_ms": None,
            "error": None,
        }
        art_store.save_run(meta)
        _current = dict(meta)

    try:
        styles.reload_styles()
        style = styles.get_style(style_id)
        meta["style_id"] = style["id"]
        meta["style_label"] = style["label"]
        meta["style_hashtag"] = style.get("hashtag")
        meta["news_lane"] = style.get("lane")

        # 1) Single story from wire
        events, events_source, events_tap = await events_svc.get_events(
            run_id=run_id,
            lane=style.get("lane"),
            style_id=style["id"],
        )
        meta["events"] = events
        meta["events_source"] = events_source
        meta["events_tap"] = events_tap
        meta["phase"] = "art_director"
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        art_store.save_run(meta)
        _current = dict(meta)

        # 2) Classic art director brief (the path that made cooler images)
        art_brief = await xai_chat.craft_art_brief(events, style)
        meta["art_brief"] = art_brief
        meta["phase"] = "compose"
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        art_store.save_run(meta)
        _current = dict(meta)

        # 3) Style seed + brief + franchise lock → Imagine
        art_prompt = styles.build_imagine_prompt(art_brief, style)
        meta["art_prompt"] = art_prompt
        meta["phase"] = "imagine"
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        art_store.save_run(meta)
        _current = dict(meta)

        image_bytes, img_stats = await asyncio.to_thread(
            xai_imagine.generate_image, art_prompt, run_id, style["label"]
        )
        meta["egress_bytes"] = img_stats.get("egress_bytes", 0)
        meta["image_model"] = img_stats.get("model")
        meta["image_source"] = img_stats.get("source")
        meta["phase"] = "stream"
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        art_store.save_run(meta, image_bytes=image_bytes)
        _current = dict(meta)

        # 4) Generative Stream = X post body (single story, full text, no poem, no hashtags)
        stream_slug = await xai_chat.craft_stream_slug(events)
        meta["stream_slug"] = stream_slug
        meta["caption"] = stream_slug
        meta["phase"] = "done"
        meta["status"] = "complete"
        ended = datetime.now(timezone.utc)
        meta["latency_ms"] = int((ended - started).total_seconds() * 1000)
        meta["updated_at"] = ended.isoformat()
        art_store.save_run(meta)
        _current = dict(meta)

        if settings.AUTO_PUBLISH and not settings.DRY_RUN:
            meta["phase"] = "publish"
            meta["updated_at"] = datetime.now(timezone.utc).isoformat()
            art_store.save_run(meta)
            _current = dict(meta)
            try:
                from services import x_publish

                pub = await asyncio.to_thread(x_publish.publish_run, run_id, False)
                meta["auto_publish"] = {
                    "ok": True,
                    "x_url": pub.get("x_url"),
                    "reply_count": pub.get("reply_count"),
                }
            except Exception as e:
                meta["auto_publish"] = {
                    "ok": False,
                    "error": f"{type(e).__name__}: {e}",
                }
            meta["phase"] = "done"
            meta["updated_at"] = datetime.now(timezone.utc).isoformat()
            art_store.save_run(meta)
            _current = dict(meta)

        _push_history(meta)
        return meta

    except Exception as e:
        meta["status"] = "failed"
        meta["phase"] = meta.get("phase") or "error"
        meta["error"] = f"{type(e).__name__}: {e}"
        meta["traceback"] = traceback.format_exc()[-2000:]
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        try:
            art_store.save_run(meta)
        except Exception:
            pass
        _current = dict(meta)
        _push_history(meta)
        raise
