"""Optional in-process hourly scheduler. Off by default."""

from __future__ import annotations

import logging
import random

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings

log = logging.getLogger("tuna-starlink.scheduler")
_scheduler: AsyncIOScheduler | None = None


def _parse_cron(expr: str) -> CronTrigger:
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(f"SCHEDULE_CRON must be 5-field cron, got {expr!r}")
    minute, hour, day, month, day_of_week = parts
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )


def _pick_style_id() -> str | None:
    """Random style from styles.yaml for scheduled runs (manual UI still picks its own)."""
    from services import styles

    styles.reload_styles()
    ids = [s["id"] for s in styles.list_styles()]
    if not ids:
        return None  # fall back to DEFAULT_STYLE inside pipeline
    return random.choice(ids)


async def _job() -> None:
    from services import pipeline

    style_id = _pick_style_id()
    log.info("scheduled generate starting style=%s", style_id or "(default)")
    try:
        meta = await pipeline.run_generate(style_id=style_id, force=False)
        log.info(
            "scheduled generate complete run=%s style=%s status=%s",
            meta.get("run_id"),
            meta.get("style_id"),
            meta.get("status"),
        )
    except Exception as e:
        log.warning("scheduled generate failed style=%s: %s", style_id, e)


def start_scheduler() -> AsyncIOScheduler | None:
    global _scheduler
    if not settings.SCHEDULE_ENABLED or not settings.SCHEDULE_CRON.strip():
        log.info("scheduler disabled (SCHEDULE_ENABLED=%s)", settings.SCHEDULE_ENABLED)
        return None
    if _scheduler is not None:
        return _scheduler
    sched = AsyncIOScheduler()
    trigger = _parse_cron(settings.SCHEDULE_CRON.strip())
    sched.add_job(_job, trigger=trigger, id="planethack-hourly", replace_existing=True)
    sched.start()
    _scheduler = sched
    log.info("scheduler started cron=%s", settings.SCHEDULE_CRON)
    return sched


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
