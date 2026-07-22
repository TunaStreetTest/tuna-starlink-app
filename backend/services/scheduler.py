"""Peak-window scheduler — few posts, short evening, hard daily cap.

Cost: each fire = 1 Imagine image (+ 2 cheap chat calls) + optional X post.
Default ~5 fires max per local day inside a 3h window every 40m.
"""

from __future__ import annotations

import json
import logging
import random
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings

log = logging.getLogger("tuna-starlink.scheduler")
_scheduler: AsyncIOScheduler | None = None
_COUNTER_NAME = ".schedule_counter.json"


def _tz() -> ZoneInfo:
    name = (settings.SCHEDULE_TIMEZONE or "America/New_York").strip()
    return ZoneInfo(name)


def _counter_path() -> Path:
    from services import art_store

    return art_store.art_root() / _COUNTER_NAME


def _load_counter() -> dict:
    path = _counter_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_counter(data: dict) -> None:
    import os

    path = _counter_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def schedule_day_stats(now: datetime | None = None) -> dict:
    """Local-day counters for health / status."""
    tz = _tz()
    now = now or datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)
    day = now.date().isoformat()
    data = _load_counter()
    if data.get("day") != day:
        return {
            "day": day,
            "runs": 0,
            "max_runs": int(settings.SCHEDULE_MAX_RUNS_PER_DAY or 0),
            "remaining": int(settings.SCHEDULE_MAX_RUNS_PER_DAY or 0),
        }
    runs = int(data.get("runs") or 0)
    cap = max(0, int(settings.SCHEDULE_MAX_RUNS_PER_DAY or 0))
    return {
        "day": day,
        "runs": runs,
        "max_runs": cap,
        "remaining": max(0, cap - runs) if cap else None,
        "last_run_id": data.get("last_run_id"),
        "last_at": data.get("last_at"),
    }


def _record_run(run_id: str | None, now: datetime) -> int:
    day = now.date().isoformat()
    data = _load_counter()
    if data.get("day") != day:
        data = {"day": day, "runs": 0}
    data["runs"] = int(data.get("runs") or 0) + 1
    data["last_run_id"] = run_id
    data["last_at"] = now.isoformat()
    _save_counter(data)
    return int(data["runs"])


def in_peak_window(now: datetime | None = None) -> bool:
    """True if local time is in [start_hour, end_hour)."""
    tz = _tz()
    now = now or datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)
    start_h = int(settings.SCHEDULE_PEAK_START_HOUR if settings.SCHEDULE_PEAK_START_HOUR is not None else 19)
    end_h = int(settings.SCHEDULE_PEAK_END_HOUR if settings.SCHEDULE_PEAK_END_HOUR is not None else 22)
    # Guard inverted/equal windows
    if end_h <= start_h:
        end_h = start_h + 1
    minutes = now.hour * 60 + now.minute
    start = start_h * 60
    end = end_h * 60
    return start <= minutes < end


def _pick_style_id() -> str | None:
    from services import styles

    styles.reload_styles()
    ids = [s["id"] for s in styles.list_styles()]
    if not ids:
        return None
    return random.choice(ids)


async def _job() -> None:
    from services import pipeline

    now = datetime.now(_tz())
    if not in_peak_window(now):
        log.info(
            "skip scheduled run outside peak window now=%s tz=%s",
            now.isoformat(),
            settings.SCHEDULE_TIMEZONE,
        )
        return

    cap = max(0, int(settings.SCHEDULE_MAX_RUNS_PER_DAY or 0))
    stats = schedule_day_stats(now)
    if cap and stats["runs"] >= cap:
        log.info(
            "skip scheduled run — daily cap reached runs=%s max=%s day=%s",
            stats["runs"],
            cap,
            stats["day"],
        )
        return

    style_id = _pick_style_id()
    log.info(
        "scheduled generate starting style=%s tz=%s interval=%sm day_runs=%s/%s",
        style_id or "(default)",
        settings.SCHEDULE_TIMEZONE,
        settings.SCHEDULE_INTERVAL_MINUTES,
        stats["runs"],
        cap or "∞",
    )
    try:
        meta = await pipeline.run_generate(style_id=style_id, force=False)
        n = _record_run(meta.get("run_id"), now)
        log.info(
            "scheduled generate complete run=%s style=%s lane=%s src=%s status=%s day_runs=%s/%s",
            meta.get("run_id"),
            meta.get("style_id"),
            meta.get("news_lane"),
            meta.get("events_source"),
            meta.get("status"),
            n,
            cap or "∞",
        )
    except Exception as e:
        log.warning("scheduled generate failed style=%s: %s", style_id, e)


def start_scheduler() -> AsyncIOScheduler | None:
    global _scheduler
    if not settings.SCHEDULE_ENABLED:
        log.info("scheduler disabled (SCHEDULE_ENABLED=%s)", settings.SCHEDULE_ENABLED)
        return None
    if _scheduler is not None:
        return _scheduler

    minutes = max(5, int(settings.SCHEDULE_INTERVAL_MINUTES or 40))
    tz = _tz()
    sched = AsyncIOScheduler(timezone=tz)
    # Fire every N minutes; job no-ops outside peak window and past daily cap.
    sched.add_job(
        _job,
        trigger=IntervalTrigger(minutes=minutes, timezone=tz),
        id="planethack-peak",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    sched.start()
    _scheduler = sched
    log.info(
        "scheduler started interval=%sm tz=%s window=%02d:00-%02d:00 max_runs/day=%s",
        minutes,
        settings.SCHEDULE_TIMEZONE,
        int(settings.SCHEDULE_PEAK_START_HOUR or 19),
        int(settings.SCHEDULE_PEAK_END_HOUR or 22),
        settings.SCHEDULE_MAX_RUNS_PER_DAY,
    )
    return sched


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
