from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from routers import gallery, generate, health, publish
from services import art_store, scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    art_store.art_root()  # ensure writable path exists
    scheduler.start_scheduler()
    yield
    scheduler.stop_scheduler()


app = FastAPI(title="TunaStarLink — Planet Hack", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(gallery.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(publish.router, prefix="/api")


@app.get("/api")
async def api_root():
    return {
        "name": settings.APP_NAME,
        "product": "Planet Hack",
        "ok": True,
        "dry_run": settings.DRY_RUN,
    }


_static = Path(__file__).parent / "static"
if _static.is_dir():
    app.mount("/", StaticFiles(directory=_static, html=True), name="static")
