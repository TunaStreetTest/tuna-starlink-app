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

    x_ok = x_credentials_ready()
    services["x"] = {
        "ok": x_ok,
        "handle": settings.X_ACCOUNT_HANDLE,
        "note": "ready for image post + brief/events comment thread when keys are set",
    }

    overall = services["disk"]["ok"] and services["xai"]["ok"]
    return {
        "ok": overall,
        "app": settings.APP_NAME,
        "edge_text": settings.EDGE_TEXT,
        "art_path": str(Path(settings.ART_STORAGE_PATH).expanduser().resolve()),
        "services": services,
    }
