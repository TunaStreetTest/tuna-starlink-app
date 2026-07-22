"""Filesystem gallery: one directory per run with atomic JSON sidecars."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings


def art_root() -> Path:
    root = Path(settings.ART_STORAGE_PATH).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def run_dir(run_id: str) -> Path:
    return art_root() / run_id


def meta_path(run_id: str) -> Path:
    return run_dir(run_id) / "meta.json"


def image_path(run_id: str) -> Path:
    return run_dir(run_id) / "art.png"


def save_run(meta: dict[str, Any], image_bytes: bytes | None = None) -> dict[str, Any]:
    run_id = meta["run_id"]
    d = run_dir(run_id)
    d.mkdir(parents=True, exist_ok=True)
    if image_bytes is not None:
        img = image_path(run_id)
        fd, tmp = tempfile.mkstemp(dir=str(d), suffix=".png.tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(image_bytes)
            os.replace(tmp, img)
            meta["image_file"] = "art.png"
            meta["image_bytes"] = len(image_bytes)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    meta.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
    _atomic_write_json(meta_path(run_id), meta)
    return meta


def load_run(run_id: str) -> dict[str, Any] | None:
    p = meta_path(run_id)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def list_runs(limit: int = 100) -> list[dict[str, Any]]:
    root = art_root()
    runs: list[dict[str, Any]] = []
    if not root.is_dir():
        return runs
    for child in sorted(root.iterdir(), reverse=True):
        if not child.is_dir():
            continue
        meta = load_run(child.name)
        if meta:
            runs.append(meta)
        if len(runs) >= limit:
            break
    return runs


def disk_stats() -> dict[str, Any]:
    root = art_root()
    total_bytes = 0
    count = 0
    for child in root.iterdir() if root.is_dir() else []:
        if not child.is_dir():
            continue
        count += 1
        for f in child.rglob("*"):
            if f.is_file():
                total_bytes += f.stat().st_size
    return {
        "path": str(root),
        "runs": count,
        "bytes": total_bytes,
        "ok": root.is_dir() and os.access(root, os.W_OK),
    }
