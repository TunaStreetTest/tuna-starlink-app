"""Peak-window scheduler: 7–10pm America/New_York, every N minutes."""

from __future__ import annotations

import logging
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings

log = logging.getLogger("tuna-starlink.scheduler")
_scheduler: AsyncIOScheduler | None = None


def _tz() -> ZoneInfo:
    name = (settings.SCHEDULE_TIMEZONE or "America/New_York").strip()
    return ZoneInfo(name)


def in_peak_window(now: datetime | None = None) -> bool:
    """True if local time is [19:00, 23:00) Eastern — 7pm through 10pm hour."""
    tz = _tz()
    now = now or datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)
    minutes = now.hour * 60 + now.minute
    start = 19 * 60  # 7:00pm
    end = 23 * 60  # exclusive 11:00pm → includes 10:00–10:59
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

    style_id = _pick_style_id()
    log.info(
        "scheduled generate starting style=%s tz=%s interval=%sm",
        style_id or "(default)",
        settings.SCHEDULE_TIMEZONE,
        settings.SCHEDULE_INTERVAL_MINUTES,
    )
    try:
        meta = await pipeline.run_generate(style_id=style_id, force=False)
        log.info(
            "scheduled generate complete run=%s style=%s lane=%s src=%s status=%s",
            meta.get("run_id"),
            meta.get("style_id"),
            meta.get("news_lane"),
            meta.get("events_source"),
            meta.get("status"),
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

    minutes = max(1, int(settings.SCHEDULE_INTERVAL_MINUTES or 21))
    tz = _tz()
    sched = AsyncIOScheduler(timezone=tz)
    # Fire every N minutes; job itself no-ops outside 7–10pm Eastern.
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
        "scheduler started interval=%sm tz=%s window=19:00-22:59 local (7–10pm Eastern)",
        minutes,
        settings.SCHEDULE_TIMEZONE,
    )
    return sched


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
