"""Planet Hack generation pipeline."""

from __future__ import annotations

import asyncio
import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from config import settings
from services import art_store, events as events_svc, styles, xai_chat, xai_imagine

log = logging.getLogger("tuna-starlink.pipeline")

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
        "batch": _batch,
    }


_batch_gate = asyncio.Lock()
_batch_task: asyncio.Task | None = None
_batch: dict[str, Any] | None = None


def _panel_snapshot(meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "style_id": meta.get("style_id"),
        "style_label": meta.get("style_label"),
        "status": meta.get("status") or "queued",
        "phase": meta.get("phase"),
        "run_id": meta.get("run_id"),
        "error": meta.get("error"),
        "latency_ms": meta.get("latency_ms"),
        "egress_bytes": meta.get("egress_bytes"),
    }


def _publish_current(meta: dict[str, Any]) -> None:
    """Mirror the live run onto the matching type panel, when a batch is open."""
    global _current
    _current = dict(meta)
    if not _batch or not _batch.get("active"):
        return
    sid = meta.get("style_id")
    panels = _batch.get("panels") or {}
    if sid in panels:
        panels[sid] = _panel_snapshot(meta)


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


def _stamp_style(meta: dict[str, Any], style: dict[str, Any]) -> None:
    meta["style_id"] = style["id"]
    meta["style_label"] = style["label"]
    meta["style_hashtag"] = style.get("hashtag")
    meta["style_version"] = style.get("version") or "core"
    meta["news_lane"] = style.get("lane")
    meta["series"] = style.get("series_name")


async def run_generate(
    style_id: str | None = None,
    force: bool = False,
    match_story: bool = False,
) -> dict[str, Any]:
    global _current

    async with _lock:
        if _current and _current.get("status") == "running" and not force:
            raise RuntimeError(
                f"generation already running: {_current.get('run_id')} "
                "(pass force=true only if you really mean it)"
            )
        run_id = art_store.new_run_id()
        styles.reload_styles()
        style = None if match_story else styles.get_style(style_id)
        started = datetime.now(timezone.utc)
        meta: dict[str, Any] = {
            "run_id": run_id,
            "status": "running",
            "phase": "events",
            "style_id": "",
            "style_label": "",
            "style_hashtag": "",
            "style_version": "",
            "news_lane": "",
            "series": "",
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
        if style:
            _stamp_style(meta, style)
        art_store.save_run(meta)
        _publish_current(meta)

    try:
        styles.reload_styles()
        if match_story:
            # The story picks the core. A version of that core is the skin.
            events, events_source, events_tap = await events_svc.get_events(
                run_id=run_id,
                any_lane=True,
            )
            style = styles.style_for_story(events)
        else:
            style = styles.get_style(style_id)
            events, events_source, events_tap = await events_svc.get_events(
                run_id=run_id,
                lane=style.get("lane"),
                style_id=style["id"],
            )
        _stamp_style(meta, style)
        meta["events"] = events
        meta["events_source"] = events_source
        meta["events_tap"] = events_tap
        meta["phase"] = "art_director"
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        art_store.save_run(meta)
        _publish_current(meta)

        # 2) Classic art director brief (the path that made cooler images)
        art_brief = await xai_chat.craft_art_brief(events, style)
        meta["art_brief"] = art_brief
        meta["phase"] = "compose"
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        art_store.save_run(meta)
        _publish_current(meta)

        # 3) Style seed + brief + franchise lock → Imagine
        art_prompt = styles.build_imagine_prompt(art_brief, style, events)
        meta["art_prompt"] = art_prompt
        meta["phase"] = "imagine"
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        art_store.save_run(meta)
        _publish_current(meta)

        image_bytes, img_stats = await asyncio.to_thread(
            xai_imagine.generate_image, art_prompt, run_id, style["label"]
        )
        meta["egress_bytes"] = img_stats.get("egress_bytes", 0)
        meta["image_model"] = img_stats.get("model")
        meta["image_source"] = img_stats.get("source")
        meta["phase"] = "stream"
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        art_store.save_run(meta, image_bytes=image_bytes)
        _publish_current(meta)

        # 4) Ledger facts (source-only) + Tuna Starlink X body (voice, facts from wire)
        stream_slug = await xai_chat.craft_stream_slug(events)
        caption = await xai_chat.craft_tuna_post(events, style, art_brief)
        meta["stream_slug"] = stream_slug
        meta["caption"] = caption
        meta["post_chars"] = len(caption or "")
        meta["phase"] = "done"
        meta["status"] = "complete"
        ended = datetime.now(timezone.utc)
        meta["latency_ms"] = int((ended - started).total_seconds() * 1000)
        meta["updated_at"] = ended.isoformat()
        art_store.save_run(meta)
        _publish_current(meta)

        # Retire wire story for this complete run (X + RSS; durable ledger).
        # get_events already marks on tap; this re-asserts after success and
        # covers any path that skipped mid-tap persistence.
        if not settings.DRY_RUN:
            try:
                events_svc.mark_run_stories_used(meta, posted=False)
            except Exception:
                log.warning("mark_run_stories_used failed run=%s", run_id, exc_info=True)

        if settings.AUTO_PUBLISH and not settings.DRY_RUN:
            meta["phase"] = "publish"
            meta["updated_at"] = datetime.now(timezone.utc).isoformat()
            art_store.save_run(meta)
            _publish_current(meta)
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
            _publish_current(meta)

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
        _publish_current(meta)
        _push_history(meta)
        raise


async def start_style_batch(style_ids: list[str], force: bool = False) -> dict[str, Any]:
    """Queue one plate per type. They run in order so each gets its own wire story."""
    global _batch, _batch_task

    ordered: list[str] = []
    labels: dict[str, str] = {}
    seen: set[str] = set()
    for raw in style_ids:
        style = styles.get_style(raw)
        sid = str(style["id"])
        if sid in seen:
            continue
        seen.add(sid)
        ordered.append(sid)
        labels[sid] = str(style.get("label") or sid)
    if not ordered:
        raise ValueError("no styles to generate")

    async with _batch_gate:
        if _batch and _batch.get("active"):
            raise RuntimeError("generation already running — one plate per type is queued")
        if _current and _current.get("status") == "running" and not force:
            raise RuntimeError(
                f"generation already running: {_current.get('run_id')} "
                "(pass force=true only if you really mean it)"
            )
        batch_id = "batch-" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        panels = {
            sid: {
                "style_id": sid,
                "style_label": labels[sid],
                "status": "queued",
                "phase": None,
                "run_id": None,
                "error": None,
            }
            for sid in ordered
        }
        _batch = {
            "id": batch_id,
            "active": True,
            "styles": ordered,
            "panels": panels,
        }
        _batch_task = asyncio.create_task(_drain_batch(batch_id, ordered, force))
        return _batch


async def wait_batch() -> None:
    task = _batch_task
    if task is not None:
        await task


async def _drain_batch(batch_id: str, style_ids: list[str], force_first: bool) -> None:
    global _batch
    try:
        for index, sid in enumerate(style_ids):
            if _batch is None or _batch.get("id") != batch_id:
                return
            panel = _batch["panels"].get(sid) or {"style_id": sid}
            panel["status"] = "running"
            panel["phase"] = "events"
            _batch["panels"][sid] = panel
            try:
                meta = await run_generate(
                    style_id=sid,
                    force=bool(force_first and index == 0),
                )
                if _batch and _batch.get("id") == batch_id:
                    _batch["panels"][sid] = _panel_snapshot(meta)
            except Exception as e:
                log.warning("batch style failed style=%s: %s", sid, e)
                if _batch and _batch.get("id") == batch_id:
                    failed = dict(_batch["panels"].get(sid) or {"style_id": sid})
                    failed["status"] = "failed"
                    failed["error"] = f"{type(e).__name__}: {e}"
                    _batch["panels"][sid] = failed
    finally:
        if _batch and _batch.get("id") == batch_id:
            _batch["active"] = False
