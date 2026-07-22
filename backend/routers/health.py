from pathlib import Path

import httpx
from fastapi import APIRouter

from config import settings
from services import art_store

router = APIRouter()


@router.get("/health")
async def health():
    services: dict = {}

    # Disk / art store
    disk = art_store.disk_stats()
    services["disk"] = {"ok": disk["ok"], **disk}

    # xAI key present (don't call paid APIs on health poll)
    services["xai"] = {
        "ok": bool(settings.XAI_API_KEY) or settings.DRY_RUN,
        "dry_run": settings.DRY_RUN,
        "chat_model": settings.XAI_CHAT_MODEL,
        "image_model": settings.XAI_IMAGE_MODEL,
        "key_present": bool(settings.XAI_API_KEY),
        "note": "chat uses non-reasoning by default; Imagine is the main $ cost",
    }

    # Optional Lemonade
    if settings.EDGE_TEXT == "lemonade":
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # Lemonade may expose /api/v1/models or OpenAI-style /v1/models
                urls = [
                    f"{settings.LEMONADE_URL.rstrip('/')}/api/v1/models",
                    f"{settings.LEMONADE_URL.rstrip('/')}/v1/models",
                ]
                ok = False
                last_err = None
                for u in urls:
                    try:
                        r = await client.get(u)
                        if r.status_code < 500:
                            ok = True
                            break
                    except Exception as e:
                        last_err = str(e)
                services["lemonade"] = {
                    "ok": ok,
                    "url": settings.LEMONADE_URL,
                    "error": None if ok else last_err,
                }
        except Exception as e:
            services["lemonade"] = {"ok": False, "error": str(e)}

    from services.x_publish import x_credentials_ready
    from services import x_search

    x_ok = x_credentials_ready()
    services["x"] = {
        "ok": x_ok,
        "handle": settings.X_ACCOUNT_HANDLE,
        "search_enabled": settings.X_SEARCH_ENABLED,
        "search_ttl_minutes": settings.X_SEARCH_TTL_MINUTES,
        "search_cache": x_search.cache_stats(),
        "note": "post+media only; recent-search OFF unless X_SEARCH_ENABLED=true",
    }

    from services import events as events_svc
    from services import scheduler as sched_svc

    services["news"] = {
        "ok": True,
        "source": settings.EVENTS_SOURCE,
        "rss_ttl_minutes": settings.RSS_INGEST_TTL_MINUTES,
        "stream": events_svc.stream_stats(),
    }
    services["schedule"] = {
        "ok": True,
        "enabled": settings.SCHEDULE_ENABLED,
        "interval_minutes": settings.SCHEDULE_INTERVAL_MINUTES,
        "peak_start_hour": settings.SCHEDULE_PEAK_START_HOUR,
        "peak_end_hour": settings.SCHEDULE_PEAK_END_HOUR,
        "max_runs_per_day": settings.SCHEDULE_MAX_RUNS_PER_DAY,
        "day": sched_svc.schedule_day_stats(),
        "auto_publish": settings.AUTO_PUBLISH,
    }

    overall = services["disk"]["ok"] and services["xai"]["ok"]
    return {
        "ok": overall,
        "app": settings.APP_NAME,
        "edge_text": settings.EDGE_TEXT,
        "art_path": str(Path(settings.ART_STORAGE_PATH).expanduser().resolve()),
        "services": services,
    }
