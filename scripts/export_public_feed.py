#!/usr/bin/env python3
"""Export a public Planet Hack feed from local art runs.

Writes feed.json plus resized JPEGs. The file is a whitelist: prompts, stream
internals, paths, and secrets never leave the studio machine.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

RUN_ID = re.compile(r"^[A-Za-z0-9_-]+$")
ROOT = Path(__file__).resolve().parents[1]
_MISSING = datetime.min.replace(tzinfo=timezone.utc)


def art_root_default() -> Path:
    return ROOT / "art"


def out_default() -> Path:
    return ROOT / "public" / "public"


def load_meta(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def stamp(meta: dict) -> datetime:
    raw = meta.get("created_at")
    if isinstance(raw, str) and raw.strip():
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return _MISSING
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    return _MISSING


def _one_line(text: str, limit: int) -> str:
    return " ".join(text.split())[:limit]


def headline(meta: dict) -> str:
    tap = meta.get("events_tap")
    if isinstance(tap, dict):
        title = tap.get("primary_title")
        if isinstance(title, str) and title.strip():
            return _one_line(title, 240)
    events = meta.get("events")
    if isinstance(events, str):
        for line in events.splitlines():
            line = line.strip().lstrip("-").strip()
            if line:
                return _one_line(line, 240)
    caption = meta.get("caption")
    if isinstance(caption, str) and caption.strip():
        first = caption.strip().splitlines()[0]
        return _one_line(first, 240)
    return "Planet Hack"


def caption_of(meta: dict) -> str:
    caption = meta.get("caption")
    if not isinstance(caption, str):
        return ""
    return caption.strip()[:4000]


def x_url_of(meta: dict) -> str | None:
    url = meta.get("x_url")
    if isinstance(url, str) and url.startswith("https://"):
        return url
    return None


def skip_reason(folder: Path, meta: dict) -> str | None:
    """None means the plate belongs on the public set."""
    if folder.name == "experiments" or folder.name.startswith("."):
        return "hidden"
    if not RUN_ID.match(folder.name):
        return "bad-id"
    if meta.get("status") != "complete":
        return "status"
    if meta.get("dry_run") is True:
        return "dry-run"
    if not (folder / "art.png").is_file():
        return "no-image"
    return None


def resize_jpeg(src: Path, dest: Path, width: int = 1280) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        frame = im.convert("RGB")
        frame.thumbnail((width, width), Image.Resampling.LANCZOS)
        frame.save(dest, "JPEG", quality=82, optimize=True)


def collect(art: Path) -> tuple[list[dict], dict[str, int]]:
    posts: list[tuple[datetime, dict]] = []
    skipped: dict[str, int] = {}
    if not art.is_dir():
        return [], skipped
    for folder in art.iterdir():
        if not folder.is_dir():
            continue
        meta_path = folder / "meta.json"
        if not meta_path.is_file():
            skipped["no-meta"] = skipped.get("no-meta", 0) + 1
            continue
        meta = load_meta(meta_path)
        if meta is None:
            skipped["bad-meta"] = skipped.get("bad-meta", 0) + 1
            continue
        reason = skip_reason(folder, meta)
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        at = stamp(meta)
        post = {
            "id": folder.name,
            "headline": headline(meta),
            "caption": caption_of(meta),
            "at": "" if at == _MISSING else at.isoformat(),
            "image": f"/media/{folder.name}.jpg",
        }
        url = x_url_of(meta)
        if url:
            post["x_url"] = url
        posts.append((at, post))
    posts.sort(key=lambda item: item[0], reverse=True)
    return [post for _, post in posts], skipped


def export_feed(art: Path, out: Path, width: int = 1280) -> dict:
    posts, skipped = collect(art)
    media = out / "media"
    media.mkdir(parents=True, exist_ok=True)
    wanted = {post["id"] for post in posts}
    for old in media.glob("*.jpg"):
        if old.stem not in wanted:
            old.unlink()
    for post in posts:
        resize_jpeg(art / post["id"] / "art.png", media / f"{post['id']}.jpg", width=width)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "posts": posts,
    }
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "feed.json"
    tmp = dest.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(dest)
    return {"count": len(posts), "skipped": skipped, "path": str(dest)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the public Planet Hack feed")
    parser.add_argument("--art", type=Path, default=art_root_default())
    parser.add_argument("--out", type=Path, default=out_default())
    parser.add_argument("--width", type=int, default=1280)
    args = parser.parse_args()
    result = export_feed(args.art, args.out, width=args.width)
    print(f"exported {result['count']} plates → {result['path']}")
    if result["skipped"]:
        parts = ", ".join(f"{key}={value}" for key, value in sorted(result["skipped"].items()))
        print(f"skipped {parts}")


if __name__ == "__main__":
    main()
