"""Hourly scheduler — one plate at minute 0, all day, America/New_York.

Cost: each fire = 1 Imagine image (+ 2 chat calls) + one X post.
Peak window and the daily cap are not applied, even when the env still names them.
"""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings

log = logging.getLogger("tuna-starlink.scheduler")
_scheduler: AsyncIOScheduler | None = None
_COUNTER_NAME = ".schedule_counter.json"
_fired_hour: str | None = None
_inflight = False


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


def hour_key(now: datetime) -> str:
    """Clock hour in the schedule zone, `YYYY-MM-DDTHH`."""
    tz = _tz()
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)
    return now.strftime("%Y-%m-%dT%H")


def claim_hour(hour: str) -> bool:
    """True the first time this clock hour fires. A second fire in the hour is skipped."""
    global _fired_hour
    if _fired_hour == hour:
        return False
    _fired_hour = hour
    return True


def hourly_trigger(tz: ZoneInfo | None = None) -> CronTrigger:
    """Minute 0 of every hour. No peak window."""
    return CronTrigger(minute=0, second=0, timezone=tz or _tz())


def wire_has_nothing(exc: BaseException) -> bool:
    text = str(exc)
    return "no event worth a plate" in text or "wire empty" in text


async def _job() -> None:
    from services import pipeline
    from services import x_publish

    global _inflight

    now = datetime.now(_tz())
    hour = hour_key(now)
    if _inflight:
        log.info("skip scheduled run — previous fire still running hour=%s", hour)
        return
    if not claim_hour(hour):
        log.info("skip scheduled run — this hour already fired hour=%s", hour)
        return

    stats = schedule_day_stats(now)
    log.info(
        "scheduled generate starting hour=%s story-led tz=%s day_runs=%s",
        hour,
        settings.SCHEDULE_TIMEZONE,
        stats["runs"],
    )
    _inflight = True
    try:
        try:
            meta = await pipeline.run_generate(match_story=True, force=False)
        except Exception as e:
            if wire_has_nothing(e):
                log.info("wire has nothing to draw hour=%s: %s", hour, e)
            else:
                log.warning("scheduled generate failed hour=%s: %s", hour, e)
            return

        n = _record_run(meta.get("run_id"), now)
        log.info(
            "scheduled generate complete run=%s style=%s version=%s lane=%s src=%s status=%s day_runs=%s",
            meta.get("run_id"),
            meta.get("style_id"),
            meta.get("style_version"),
            meta.get("news_lane"),
            meta.get("events_source"),
            meta.get("status"),
            n,
        )
        if meta.get("status") != "complete" or settings.DRY_RUN or meta.get("dry_run"):
            log.info(
                "not posting hour=%s run=%s status=%s dry_run=%s",
                hour,
                meta.get("run_id"),
                meta.get("status"),
                settings.DRY_RUN or meta.get("dry_run"),
            )
            return
        run_id = str(meta.get("run_id") or "")
        try:
            pub = await asyncio.to_thread(x_publish.publish_run, run_id, False)
            log.info(
                "scheduled post run=%s hour=%s x_url=%s plate=%s",
                run_id,
                hour,
                pub.get("x_url"),
                pub.get("plate_url"),
            )
        except Exception as e:
            log.warning("scheduled publish failed run=%s hour=%s: %s", run_id, hour, e)
    finally:
        _inflight = False


def start_scheduler() -> AsyncIOScheduler | None:
    global _scheduler
    if not settings.SCHEDULE_ENABLED:
        log.info("scheduler disabled (SCHEDULE_ENABLED=%s)", settings.SCHEDULE_ENABLED)
        return None
    if _scheduler is not None:
        return _scheduler

    tz = _tz()
    sched = AsyncIOScheduler(timezone=tz)
    # Top of every hour. A fire still running is skipped (max_instances=1).
    # Peak hours and the daily cap in the env are not read.
    sched.add_job(
        _job,
        trigger=hourly_trigger(tz),
        id="planethack-hourly",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=900,
    )
    sched.start()
    _scheduler = sched
    log.info(
        "scheduler started hourly minute=0 tz=%s (peak window and daily cap ignored)",
        settings.SCHEDULE_TIMEZONE,
    )
    return sched


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
