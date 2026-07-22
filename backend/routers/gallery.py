from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services import art_store

router = APIRouter(prefix="/gallery")


@router.get("")
async def list_gallery(limit: int = 100):
    runs = art_store.list_runs(limit=limit)
    # Client-friendly shape
    out = []
    for m in runs:
        out.append(
            {
                "run_id": m.get("run_id"),
                "status": m.get("status"),
                "style_id": m.get("style_id"),
                "style_label": m.get("style_label"),
                "caption": m.get("caption"),
                "events": m.get("events"),
                "created_at": m.get("created_at"),
                "updated_at": m.get("updated_at"),
                "dry_run": m.get("dry_run"),
                "egress_bytes": m.get("egress_bytes"),
                "latency_ms": m.get("latency_ms"),
                "has_image": art_store.image_path(m["run_id"]).is_file() if m.get("run_id") else False,
                "error": m.get("error"),
            }
        )
    return {"runs": out, "count": len(out)}


@router.get("/{run_id}")
async def get_run(run_id: str):
    meta = art_store.load_run(run_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"run not found: {run_id}")
    meta = dict(meta)
    meta["has_image"] = art_store.image_path(run_id).is_file()
    # Don't dump full traceback in list UI; keep on detail if present
    return meta


@router.get("/{run_id}/image")
async def get_image(run_id: str):
    path = art_store.image_path(run_id)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="image not found")
    return FileResponse(path, media_type="image/png", filename=f"planethack_{run_id}.png")
