import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from services import pipeline, styles

router = APIRouter()


class GenerateRequest(BaseModel):
    style: str | None = None
    force: bool = False
    wait: bool = False  # true = block until complete (handy for CLI smoke tests)


@router.get("/styles")
async def get_styles():
    return {"styles": styles.list_styles()}


@router.get("/pipeline")
async def get_pipeline():
    return pipeline.pipeline_status()


@router.post("/generate")
async def generate(body: GenerateRequest, background: BackgroundTasks):
    try:
        styles.get_style(body.style)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if body.wait:
        try:
            meta = await pipeline.run_generate(style_id=body.style, force=body.force)
            return {"started": True, "waited": True, "run": meta}
        except RuntimeError as e:
            raise HTTPException(status_code=409, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e))

    async def _bg():
        try:
            await pipeline.run_generate(style_id=body.style, force=body.force)
        except Exception:
            pass  # status persisted on disk / pipeline status

    # Fire-and-forget via asyncio so FastAPI can return immediately
    asyncio.create_task(_bg())
    status = pipeline.pipeline_status()
    return {
        "started": True,
        "waited": False,
        "current": status.get("current"),
        "message": "generation started — poll /api/pipeline or /api/gallery",
    }
