"""News as a stream + X search (Session 2).

Flow per run:
  1) style → news lane
  2) try X recent search for that lane → pick ONE story
  3) else RSS stream: inject feeds, tap ONE unconsumed item in that lane
  4) last resort: any unconsumed / recycle
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

_RSS_FEEDS: tuple[tuple[str, str, str], ...] = (
    # source_id, url, default_lane
    ("bbc-world", "https://feeds.bbci.co.uk/news/world/rss.xml", "geopolitics"),
    ("bbc-tech", "https://feeds.bbci.co.uk/news/technology/rss.xml", "tech"),
    ("bbc-business", "https://feeds.bbci.co.uk/news/business/rss.xml", "markets"),
    ("bbc-science", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "science"),
    ("nyt-world", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "geopolitics"),
    ("nyt-tech", "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", "tech"),
    ("nyt-science", "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml", "science"),
    ("nyt-business", "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "markets"),
    ("guardian-world", "https://www.theguardian.com/world/rss", "geopolitics"),
    ("guardian-tech", "https://www.theguardian.com/uk/technology/rss", "tech"),
    ("aljazeera", "https://www.aljazeera.com/xml/rss/all.xml", "geopolitics"),
    ("npr-world", "https://feeds.npr.org/1004/rss.xml", "geopolitics"),
    ("npr-news", "https://feeds.npr.org/1001/rss.xml", "geopolitics"),
)

_LANE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "geopolitics": (
        "war", "ceasefire", "sanctions", "diplomat", "election", "nato", "military",
        "invasion", "treaty", "president", "minister", "border", "missile", "ukraine",
        "israel", "gaza", "iran", "china", "russia", "un ", "security council",
    ),
    "tech": (
        "ai ", "artificial intelligence", "chip", "semiconductor", "cyber", "hack",
        "software", "openai", "google", "apple", "microsoft", "nvidia", "gpu",
        "startup", "app ", "internet", "crypto", "bitcoin", "robot",
    ),
    "science": (
        "nasa", "space", "climate", "energy", "fusion", "quantum", "research",
        "scientist", "storm", "wildfire", "earthquake", "virus", "vaccine",
        "telescope", "mars", "ocean", "species", "physics",
    ),
    "markets": (
        "market", "stock", "tariff", "fed ", "inflation", "bank", "trade",
        "protest", "strike", "gdp", "recession", "bond", "dollar", "oil price",
        "layoff", "earnings", "wall street", "economy",
    ),
}

_STREAM_NAME = ".news_stream.json"
_STREAM_MAX_ITEMS = 800
_TAP_SIZE = 1  # Session 2: single story


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


def _infer_lane(title: str, summary: str, default: str) -> str:
    blob = f"{title} {summary}".lower()
    scores = {lane: 0 for lane in _LANE_KEYWORDS}
    for lane, kws in _LANE_KEYWORDS.items():
        for kw in kws:
            if kw in blob:
                scores[lane] += 1
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return default
    return best


def _parse_rss_items(
    xml_bytes: bytes, source: str, default_lane: str, limit: int = 40
) -> list[dict[str, Any]]:
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
        lane = _infer_lane(title, desc, default_lane)
        items.append(
            {
                "id": _item_id(source, guid, link, title),
                "title": title,
                "line": line,
                "source": source,
                "lane": lane,
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
    import os

    path = _stream_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now()
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
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
    if len(items) <= _STREAM_MAX_ITEMS:
        return items
    unconsumed = [i for i in items if not i.get("consumed_at")]
    consumed = [i for i in items if i.get("consumed_at")]
    unconsumed.sort(key=lambda x: x.get("ingested_at") or "", reverse=True)
    consumed.sort(key=lambda x: x.get("consumed_at") or "", reverse=True)
    keep = unconsumed[:_STREAM_MAX_ITEMS]
    if len(keep) < _STREAM_MAX_ITEMS:
        keep.extend(consumed[: _STREAM_MAX_ITEMS - len(keep)])
    return keep


async def ingest_feeds() -> dict[str, int]:
    stream = _load_stream()
    by_id = {i["id"]: i for i in stream.get("items") or [] if i.get("id")}
    new_count = 0
    feed_ok = 0
    feed_fail = 0

    async with httpx.AsyncClient(
        timeout=12.0,
        follow_redirects=True,
        headers={"User-Agent": "tuna-starlink-app/0.2 (PlanetHack news-stream)"},
    ) as http:
        for source, url, default_lane in _RSS_FEEDS:
            try:
                r = await http.get(url)
                r.raise_for_status()
                batch = _parse_rss_items(r.content, source, default_lane, limit=40)
                feed_ok += 1
                for item in batch:
                    if item["id"] not in by_id:
                        by_id[item["id"]] = item
                        new_count += 1
                    else:
                        # backfill lane if missing
                        if not by_id[item["id"]].get("lane"):
                            by_id[item["id"]]["lane"] = item["lane"]
            except Exception:
                feed_fail += 1
                continue

    items = _trim_stream(list(by_id.values()))
    stream["items"] = items
    _save_stream(stream)
    return {
        "new": new_count,
        "total": len(items),
        "unconsumed": sum(1 for i in items if not i.get("consumed_at")),
        "feeds_ok": feed_ok,
        "feeds_fail": feed_fail,
    }


def _tap_unconsumed(
    items: list[dict[str, Any]], n: int, lane: str | None
) -> list[dict[str, Any]]:
    free = [i for i in items if not i.get("consumed_at")]
    if lane:
        lane_free = [i for i in free if (i.get("lane") or "") == lane]
        if lane_free:
            free = lane_free
    free.sort(key=lambda x: x.get("ingested_at") or "", reverse=True)
    return free[:n]


def _mark_consumed(chosen: list[dict[str, Any]], run_id: str) -> None:
    stream = _load_stream()
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
    by_lane: dict[str, int] = {}
    for i in items:
        if i.get("consumed_at"):
            continue
        lane = i.get("lane") or "unknown"
        by_lane[lane] = by_lane.get(lane, 0) + 1
    return {
        "total": len(items),
        "unconsumed": sum(1 for i in items if not i.get("consumed_at")),
        "consumed": sum(1 for i in items if i.get("consumed_at")),
        "taps": stream.get("taps") or 0,
        "updated_at": stream.get("updated_at"),
        "unconsumed_by_lane": by_lane,
        "path": str(_stream_path()),
        "tap_size": _TAP_SIZE,
    }


async def get_events(
    run_id: str | None = None,
    *,
    lane: str | None = None,
    style_id: str | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """
    Return (events_text, source_label, tap_meta) for ONE story.
    Prefers X search for the style's lane; falls back to RSS stream.
    """
    if settings.DRY_RUN:
        stamp = datetime.now(timezone.utc).strftime("%H%M%S")
        return (
            format_bullets([f"Dry-run single story {stamp}: markets and power grids shift overnight"]),
            "dry-run-stream",
            {"tap_size": 1, "fresh": True, "lane": lane, "style_id": style_id},
        )

    rid = run_id or f"tap-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    lane = (lane or "geopolitics").lower().strip()
    mode = (settings.EVENTS_SOURCE or "stream").lower().strip()

    # --- 1) X search (required path when credentials present) ---
    if mode in ("stream", "rss", "hybrid", "x", "x-search") and not settings.DRY_RUN:
        try:
            from services import x_search

            best = x_search.pick_best_story(lane)
        except Exception as e:
            best = None
            x_err = str(e)
        else:
            x_err = None

        if best:
            line = best.get("line") or best.get("text") or ""
            tap_meta = {
                "tap_size": 1,
                "fresh": True,
                "lane": lane,
                "style_id": style_id,
                "item_ids": [best.get("id")],
                "sources": ["x-search"],
                "x_post_url": best.get("url"),
                "x_score": best.get("score"),
                "x_likes": best.get("likes"),
            }
            return format_bullets([line]), "x-search", tap_meta

    # --- 2) RSS stream lane-filtered tap ---
    stats = await ingest_feeds()
    stream = _load_stream()
    items = stream.get("items") or []
    chosen = _tap_unconsumed(items, _TAP_SIZE, lane)

    if not chosen:
        stats = await ingest_feeds()
        stream = _load_stream()
        items = stream.get("items") or []
        chosen = _tap_unconsumed(items, _TAP_SIZE, lane)

    recycled = False
    if not chosen:
        # any unconsumed
        chosen = _tap_unconsumed(items, _TAP_SIZE, None)
    if not chosen:
        recycled_pool = [i for i in items if i.get("consumed_at")]
        recycled_pool = [i for i in recycled_pool if (i.get("lane") or "") == lane] or recycled_pool
        recycled_pool.sort(key=lambda x: x.get("consumed_at") or "")
        chosen = recycled_pool[:_TAP_SIZE]
        recycled = bool(chosen)
        for c in chosen:
            c["consumed_at"] = None
            c["consumed_by_run"] = None

    if chosen:
        _mark_consumed(chosen, rid)
        lines = [c.get("line") or c.get("title") or "" for c in chosen if c.get("line") or c.get("title")]
        tap_meta = {
            "tap_size": len(chosen),
            "item_ids": [c["id"] for c in chosen],
            "sources": sorted({c.get("source") for c in chosen if c.get("source")}),
            "lanes": sorted({c.get("lane") for c in chosen if c.get("lane")}),
            "fresh": not recycled,
            "recycled": recycled,
            "lane": lane,
            "style_id": style_id,
            "ingest": stats,
            "stream": stream_stats(),
            "x_search_fallback": True,
        }
        src = "news-stream" if not recycled else "news-stream-recycle"
        return format_bullets(lines), src, tap_meta

    # --- 3) static fallback ---
    return (
        format_bullets(
            ["Global markets and power systems shift under pressure from competing headlines"]
        ),
        "fallback-static",
        {"fresh": False, "lane": lane, "style_id": style_id},
    )
