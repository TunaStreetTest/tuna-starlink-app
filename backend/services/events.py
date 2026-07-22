"""News as a local stream.

Mental model:
  feeds continuously inject items into a durable stream (append-only by id).
  each Planet Hack run *taps* the stream and only takes items not yet consumed.
  next tap never reuses the same headlines until the stream is exhausted and we
  recycle only as a last resort.

File-backed stream under ART_STORAGE_PATH (.news_stream.json).
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import httpx

from config import settings
from services import art_store

# Diverse free public feeds — more surface area so the stream keeps moving.
_RSS_FEEDS: tuple[tuple[str, str], ...] = (
    ("bbc-world", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("bbc-tech", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
    ("bbc-business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("bbc-science", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"),
    ("nyt-world", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("nyt-tech", "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"),
    ("nyt-science", "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml"),
    ("guardian-world", "https://www.theguardian.com/world/rss"),
    ("guardian-tech", "https://www.theguardian.com/uk/technology/rss"),
    ("aljazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("npr-world", "https://feeds.npr.org/1004/rss.xml"),
    ("npr-news", "https://feeds.npr.org/1001/rss.xml"),
)

_REFUSAL_PATTERNS = re.compile(
    r"(no access to real[- ]time|training data prior|as an ai|i (don't|do not) have|"
    r"cannot (provide|access) (live|real[- ]time)|knowledge cutoff|"
    r"current knowledge limited|i'm unable to browse)",
    re.I,
)

_STREAM_NAME = ".news_stream.json"
_STREAM_MAX_ITEMS = 800
_TAP_SIZE = 6  # headlines per generation


def events_look_like_refusal(text: str) -> bool:
    if not text or len(text.strip()) < 20:
        return True
    return bool(_REFUSAL_PATTERNS.search(text))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stream_path() -> Path:
    return art_store.art_root() / _STREAM_NAME


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return " ".join(el.text.split())


def _item_id(source: str, guid: str, link: str, title: str) -> str:
    raw = guid or link or f"{source}|{title}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def _parse_rss_items(xml_bytes: bytes, source: str, limit: int = 40) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    items: list[dict[str, Any]] = []
    for el in root.iter():
        if _local(el.tag) != "item":
            continue
        title = desc = link = guid = pub = ""
        for child in el:
            name = _local(child.tag)
            if name == "title":
                title = _text(child)
            elif name in ("description", "summary"):
                desc = _text(child)
            elif name == "link":
                link = _text(child)
            elif name == "guid":
                guid = _text(child)
            elif name in ("pubDate", "published", "date"):
                pub = _text(child)
        desc = re.sub(r"<[^>]+>", " ", desc)
        desc = " ".join(desc.split())
        if not title:
            continue
        line = title
        if desc and desc.lower() not in title.lower():
            snippet = desc[:140].rstrip()
            if snippet:
                line = f"{title} — {snippet}"
        items.append(
            {
                "id": _item_id(source, guid, link, title),
                "title": title,
                "line": line,
                "source": source,
                "link": link,
                "guid": guid,
                "published": pub,
                "ingested_at": _now(),
                "consumed_at": None,
                "consumed_by_run": None,
            }
        )
        if len(items) >= limit:
            break
    return items


def _load_stream() -> dict[str, Any]:
    path = _stream_path()
    if not path.is_file():
        return {"items": [], "updated_at": None, "taps": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"items": [], "updated_at": None, "taps": 0}
        data.setdefault("items", [])
        data.setdefault("taps", 0)
        return data
    except (json.JSONDecodeError, OSError):
        return {"items": [], "updated_at": None, "taps": 0}


def _save_stream(data: dict[str, Any]) -> None:
    path = _stream_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now()
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    import os

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _trim_stream(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep stream bounded: prefer keeping unconsumed, then newest."""
    if len(items) <= _STREAM_MAX_ITEMS:
        return items
    unconsumed = [i for i in items if not i.get("consumed_at")]
    consumed = [i for i in items if i.get("consumed_at")]
    # newest first within each bucket
    unconsumed.sort(key=lambda x: x.get("ingested_at") or "", reverse=True)
    consumed.sort(key=lambda x: x.get("consumed_at") or "", reverse=True)
    keep = unconsumed[:_STREAM_MAX_ITEMS]
    if len(keep) < _STREAM_MAX_ITEMS:
        keep.extend(consumed[: _STREAM_MAX_ITEMS - len(keep)])
    return keep


async def ingest_feeds() -> dict[str, int]:
    """Pull all feeds; append only never-seen item ids. Returns stats."""
    stream = _load_stream()
    by_id = {i["id"]: i for i in stream.get("items") or [] if i.get("id")}
    new_count = 0
    feed_ok = 0
    feed_fail = 0

    async with httpx.AsyncClient(
        timeout=12.0,
        follow_redirects=True,
        headers={"User-Agent": "tuna-starlink-app/0.1 (PlanetHack news-stream)"},
    ) as http:
        for source, url in _RSS_FEEDS:
            try:
                r = await http.get(url)
                r.raise_for_status()
                batch = _parse_rss_items(r.content, source=source, limit=40)
                feed_ok += 1
                for item in batch:
                    if item["id"] not in by_id:
                        by_id[item["id"]] = item
                        new_count += 1
            except Exception:
                feed_fail += 1
                continue

    items = list(by_id.values())
    items = _trim_stream(items)
    stream["items"] = items
    _save_stream(stream)
    return {
        "new": new_count,
        "total": len(items),
        "unconsumed": sum(1 for i in items if not i.get("consumed_at")),
        "feeds_ok": feed_ok,
        "feeds_fail": feed_fail,
    }


def _tap_unconsumed(items: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    free = [i for i in items if not i.get("consumed_at")]
    # newest ingested first so we ride the front of the stream
    free.sort(key=lambda x: x.get("ingested_at") or "", reverse=True)
    return free[:n]


def _mark_consumed(stream: dict[str, Any], chosen: list[dict[str, Any]], run_id: str) -> None:
    ids = {c["id"] for c in chosen}
    now = _now()
    for item in stream.get("items") or []:
        if item.get("id") in ids:
            item["consumed_at"] = now
            item["consumed_by_run"] = run_id
    stream["taps"] = int(stream.get("taps") or 0) + 1
    _save_stream(stream)


def format_bullets(lines: Iterable[str]) -> str:
    return "\n".join(f"- {line}" for line in lines)


def stream_stats() -> dict[str, Any]:
    stream = _load_stream()
    items = stream.get("items") or []
    return {
        "total": len(items),
        "unconsumed": sum(1 for i in items if not i.get("consumed_at")),
        "consumed": sum(1 for i in items if i.get("consumed_at")),
        "taps": stream.get("taps") or 0,
        "updated_at": stream.get("updated_at"),
        "path": str(_stream_path()),
    }


async def get_events(run_id: str | None = None) -> tuple[str, str, dict[str, Any]]:
    """
    Tap the news stream for this run.

    Returns (events_text, source_label, tap_meta).
    """
    if settings.DRY_RUN:
        stamp = datetime.now(timezone.utc).strftime("%H%M%S")
        return (
            format_bullets(
                [
                    f"Dry-run stream tap {stamp}: global summit debates climate pledges",
                    f"Dry-run stream tap {stamp}: markets react to new chip export rules",
                    f"Dry-run stream tap {stamp}: athletes rewrite a world record overnight",
                    f"Dry-run stream tap {stamp}: coastal cities brace for a rare storm system",
                    f"Dry-run stream tap {stamp}: scientists publish a deep-space signal paper",
                ]
            ),
            "dry-run-stream",
            {"tap_size": 5, "fresh": True},
        )

    mode = (settings.EVENTS_SOURCE or "rss").lower().strip()

    if mode in ("rss", "hybrid", "stream"):
        # 1) Ingest — always try to pull fresh into the stream first
        stats = await ingest_feeds()
        stream = _load_stream()
        items = stream.get("items") or []

        # 2) Tap only unconsumed
        chosen = _tap_unconsumed(items, _TAP_SIZE)

        # 3) If stream was dry of new items, one more ingest then re-tap
        if len(chosen) < max(3, _TAP_SIZE // 2):
            stats2 = await ingest_feeds()
            stats = {
                "new": stats.get("new", 0) + stats2.get("new", 0),
                "total": stats2.get("total", stats.get("total")),
                "unconsumed": stats2.get("unconsumed"),
                "feeds_ok": stats2.get("feeds_ok"),
                "feeds_fail": stats2.get("feeds_fail"),
            }
            stream = _load_stream()
            items = stream.get("items") or []
            chosen = _tap_unconsumed(items, _TAP_SIZE)

        recycled = False
        if not chosen:
            # Last resort: recycle oldest consumed so we never block generation
            recycled_pool = [i for i in items if i.get("consumed_at")]
            recycled_pool.sort(key=lambda x: x.get("consumed_at") or "")
            chosen = recycled_pool[:_TAP_SIZE]
            recycled = True
            # clear consumption so we re-mark as this run
            for c in chosen:
                c["consumed_at"] = None
                c["consumed_by_run"] = None

        if chosen:
            rid = run_id or f"tap-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            _mark_consumed(stream if not recycled else _load_stream(), chosen, rid)
            # re-load after mark if recycled path reloaded
            if recycled:
                stream = _load_stream()
                by_id = {i["id"]: i for i in stream.get("items") or []}
                for c in chosen:
                    if c["id"] in by_id:
                        by_id[c["id"]]["consumed_at"] = _now()
                        by_id[c["id"]]["consumed_by_run"] = rid
                stream["items"] = list(by_id.values())
                stream["taps"] = int(stream.get("taps") or 0) + 1
                _save_stream(stream)

            lines = [c.get("line") or c.get("title") or "" for c in chosen]
            lines = [ln for ln in lines if ln]
            tap_meta = {
                "tap_size": len(chosen),
                "item_ids": [c["id"] for c in chosen],
                "sources": sorted({c.get("source") for c in chosen if c.get("source")}),
                "fresh": not recycled,
                "recycled": recycled,
                "ingest": stats,
                "stream": stream_stats(),
            }
            src = "news-stream" if not recycled else "news-stream-recycle"
            return format_bullets(lines), src, tap_meta

    if mode in ("xai", "hybrid"):
        from services import xai_chat

        text = await xai_chat.summarize_events_llm()
        if not events_look_like_refusal(text):
            return text, "xai", {"fresh": True}

    return (
        format_bullets(
            [
                "Markets swing on unexpected rate and trade headlines",
                "Regional conflict and ceasefire talks dominate diplomacy wires",
                "Major climate and extreme weather systems disrupt coasts",
                "Big-tech and chip export rules reshape global supply chains",
                "Sports and culture moments spike global attention briefly",
            ]
        ),
        "fallback-static",
        {"fresh": False},
    )
