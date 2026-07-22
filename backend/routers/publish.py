from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import x_publish

router = APIRouter(prefix="/publish")


class PublishBody(BaseModel):
    run_id: str
    with_comments: bool = True


@router.get("/status")
async def publish_status():
    return {
        "credentials_ready": x_publish.x_credentials_ready(),
        "handle": __import__("config", fromlist=["settings"]).settings.X_ACCOUNT_HANDLE,
        "flow": {
            "main": "image + wordy caption (+ #PlanetHack)",
            "comment_1": "news headlines/keywords that fueled this piece",
        },
    }


@router.get("/preview/{run_id}")
async def preview(run_id: str):
    try:
        return x_publish.preview_post(run_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/x")
async def publish_to_x(body: PublishBody):
    try:
        return x_publish.publish_run(body.run_id, with_comments=body.with_comments)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"{type(e).__name__}: {e}")


@router.post("/x/reply")
async def publish_reply_only(body: PublishBody):
    """Repair: add the news-context comment onto an already-posted main tweet."""
    try:
        return x_publish.reply_to_existing(body.run_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"{type(e).__name__}: {e}")
