"""Lean news wire for Planet Hack — few free RSS streams, short peak evening.

Cost rules:
  - RSS only by default (free). X Recent Search is opt-in + gated (see x_search).
  - Four feeds max (one primary per lane). No NYT/Guardian/NPR fan-out.
  - Ingest is TTL-cached so back-to-back generates do not re-hit every feed.
  - Small stream file; small pack. Campaign is a few posts, not a news desk.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import httpx

from config import settings
from services import art_store

log = logging.getLogger("tuna-starlink.events")

# One solid free feed per style lane. Do not grow this list casually.
_RSS_FEEDS: tuple[tuple[str, str, str], ...] = (
    # source_id, url, default_lane
    ("bbc-world", "https://feeds.bbci.co.uk/news/world/rss.xml", "geopolitics"),
    ("bbc-tech", "https://feeds.bbci.co.uk/news/technology/rss.xml", "tech"),
    ("bbc-science", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "science"),
    ("bbc-business", "https://feeds.bbci.co.uk/news/business/rss.xml", "markets"),
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
        "telescope", "mars", "ocean", "species", "physics", "ebola", "nuclear",
    ),
    "markets": (
        "market", "stock", "tariff", "fed ", "inflation", "bank", "trade",
        "gdp", "recession", "bond", "dollar", "oil price", "layoff", "earnings",
        "wall street", "economy", "price",
    ),
}

_STREAM_NAME = ".news_stream.json"
_STREAM_MAX_ITEMS = 120
_ITEMS_PER_FEED = 12
_PACK_SIZE = 1  # single story only — full text drives stream + image
_X_SLOTS = 1
_X_MIN_SCORE = 40


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
    xml_bytes: bytes, source: str, default_lane: str, limit: int = _ITEMS_PER_FEED
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
        # Keep full summary so Generative Stream can fill the 280-char post field.
        line = title
        if desc and desc.lower() not in title.lower():
            snippet = desc[:420].rstrip()
            if snippet:
                line = f"{title} — {snippet}"
        lane = _infer_lane(title, desc, default_lane)
        items.append(
            {
                "id": _item_id(source, guid, link, title),
                "title": title,
                "line": line,
                "summary": desc[:800] if desc else "",
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


def _stream_age_minutes(stream: dict[str, Any]) -> float | None:
    raw = stream.get("updated_at") or stream.get("ingested_at")
    if not raw:
        return None
    try:
        ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds() / 60.0
    except ValueError:
        return None


async def ingest_feeds(*, force: bool = False) -> dict[str, Any]:
    """Pull lean RSS set. Skips network when stream is fresher than TTL."""
    stream = _load_stream()
    items_existing = stream.get("items") or []
    ttl = max(0, int(settings.RSS_INGEST_TTL_MINUTES or 0))
    age = _stream_age_minutes(stream)

    if (
        not force
        and ttl > 0
        and items_existing
        and age is not None
        and age < ttl
    ):
        log.info(
            "RSS ingest skipped (cache age=%.0fm ttl=%sm items=%s)",
            age,
            ttl,
            len(items_existing),
        )
        return {
            "new": 0,
            "total": len(items_existing),
            "unconsumed": sum(1 for i in items_existing if not i.get("consumed_at")),
            "feeds_ok": 0,
            "feeds_fail": 0,
            "feeds_configured": len(_RSS_FEEDS),
            "cached": True,
            "age_minutes": round(age, 1),
            "ttl_minutes": ttl,
        }

    by_id = {i["id"]: i for i in items_existing if i.get("id")}
    new_count = 0
    feed_ok = 0
    feed_fail = 0

    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
        headers={"User-Agent": "tuna-starlink-app/0.3 (PlanetHack lean-wire)"},
    ) as http:
        for source, url, default_lane in _RSS_FEEDS:
            try:
                r = await http.get(url)
                r.raise_for_status()
                batch = _parse_rss_items(
                    r.content, source, default_lane, limit=_ITEMS_PER_FEED
                )
                feed_ok += 1
                for item in batch:
                    if item["id"] not in by_id:
                        by_id[item["id"]] = item
                        new_count += 1
                    else:
                        if not by_id[item["id"]].get("lane"):
                            by_id[item["id"]]["lane"] = item["lane"]
            except Exception as e:
                feed_fail += 1
                log.warning("RSS feed failed source=%s: %s", source, e)
                continue

    items = _trim_stream(list(by_id.values()))
    stream["items"] = items
    stream["feeds"] = [f[0] for f in _RSS_FEEDS]
    _save_stream(stream)
    log.info(
        "RSS ingest done new=%s total=%s feeds_ok=%s/%s",
        new_count,
        len(items),
        feed_ok,
        len(_RSS_FEEDS),
    )
    return {
        "new": new_count,
        "total": len(items),
        "unconsumed": sum(1 for i in items if not i.get("consumed_at")),
        "feeds_ok": feed_ok,
        "feeds_fail": feed_fail,
        "feeds_configured": len(_RSS_FEEDS),
        "cached": False,
        "ttl_minutes": ttl,
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
    """Mark RSS stream items consumed. X-only items are skipped (no stream id)."""
    stream = _load_stream()
    ids = {c["id"] for c in chosen if c.get("id") and c.get("source") != "x-search"}
    if not ids:
        stream["taps"] = int(stream.get("taps") or 0) + 1
        _save_stream(stream)
        return
    now = _now()
    for item in stream.get("items") or []:
        if item.get("id") in ids:
            item["consumed_at"] = now
            item["consumed_by_run"] = run_id
    stream["taps"] = int(stream.get("taps") or 0) + 1
    _save_stream(stream)


def format_bullets(lines: Iterable[str]) -> str:
    return "\n".join(f"- {line}" for line in lines if line)


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
        "pack_size": _PACK_SIZE,
        "tap_size": _PACK_SIZE,
        "feeds": [f[0] for f in _RSS_FEEDS],
        "feeds_count": len(_RSS_FEEDS),
        "rss_ttl_minutes": int(settings.RSS_INGEST_TTL_MINUTES or 0),
        "x_search_enabled": bool(settings.X_SEARCH_ENABLED),
    }


def _dedupe_key(text: str) -> str:
    return re.sub(r"\W+", "", (text or "")[:56].lower())


def _pack_line(item: dict[str, Any]) -> str:
    """Single-story full text: title + summary — enough material to fill 280-char post."""
    title = (item.get("title") or "").strip()
    summary = re.sub(r"https?://\S+", "", (item.get("summary") or "").strip())
    summary = re.sub(r"\s+", " ", summary).strip()
    line = re.sub(r"https?://\S+", "", (item.get("line") or item.get("text") or "").strip())
    line = re.sub(r"\s+", " ", line).strip()

    # Build the longest clean single-story string available
    if title and summary and summary.lower() not in title.lower():
        body = f"{title} — {summary}"
    elif line and len(line) >= len(title):
        body = line
    elif title and line and title.lower() not in line.lower():
        body = f"{title} — {line}"
    else:
        body = line or title
    # Cap well above tweet size so craft_stream_slug can fill all 280
    return body[:900]


_PRIMARY_BOOST = re.compile(
    r"\b(hack|rogue|breach|war|ceasefire|sanction|missile|nuclear|"
    r"launch|openai|nvidia|election|storm|wildfire|ebola|vaccine|"
    r"tariff|inflation|earnings|indict)\b",
    re.I,
)


def _primary_rank(item: dict[str, Any]) -> int:
    """Higher = better primary for Generative Stream / art metaphor."""
    title = item.get("title") or item.get("line") or ""
    score = int(item.get("score") or 0)
    if item.get("source") == "x-search":
        score += 8
    if _PRIMARY_BOOST.search(title):
        score += 25
    n = len(title)
    if 40 <= n <= 140:
        score += 10
    elif n > 180:
        score -= 8
    return score


def _build_wire_pack(
    x_hits: list[dict[str, Any]],
    rss_hits: list[dict[str, Any]],
    pack_size: int = _PACK_SIZE,
) -> list[dict[str, Any]]:
    """Merge optional X + RSS into a small multi-headline pack."""
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    x_kept = 0
    for h in x_hits:
        if x_kept >= _X_SLOTS:
            break
        if (h.get("score") or 0) < _X_MIN_SCORE:
            continue
        key = _dedupe_key(h.get("title") or h.get("line") or h.get("text") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        candidates.append(
            {
                "id": h.get("id"),
                "title": h.get("title") or (h.get("line") or "")[:160],
                "line": _pack_line(h),
                "source": "x-search",
                "lane": h.get("lane"),
                "url": h.get("url"),
                "score": h.get("score"),
                "likes": h.get("likes"),
            }
        )
        x_kept += 1

    for h in rss_hits:
        if len(candidates) >= pack_size + 2:
            break
        key = _dedupe_key(h.get("title") or h.get("line") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        candidates.append(
            {
                "id": h.get("id"),
                "title": h.get("title") or (h.get("line") or "")[:160],
                "line": _pack_line(h),
                "source": h.get("source") or "rss",
                "lane": h.get("lane"),
                "link": h.get("link"),
                "score": 50,
            }
        )

    candidates.sort(key=_primary_rank, reverse=True)
    return candidates[:pack_size]


async def get_events(
    run_id: str | None = None,
    *,
    lane: str | None = None,
    style_id: str | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """
    Return (events_text, source_label, tap_meta) for a lean wire pack.

    Primary story is bullet #1 (art metaphor + Generative Stream lead).
    """
    if settings.DRY_RUN:
        stamp = datetime.now(timezone.utc).strftime("%H%M%S")
        lines = [
            f"Dry-run primary story {stamp}: markets and power grids shift overnight",
            "Dry-run secondary: chipmakers race for energy contracts",
        ]
        return (
            format_bullets(lines),
            "dry-run-stream",
            {"tap_size": len(lines), "fresh": True, "lane": lane, "style_id": style_id},
        )

    rid = run_id or f"tap-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    lane = (lane or "geopolitics").lower().strip()
    mode = (settings.EVENTS_SOURCE or "stream").lower().strip()

    # --- lean RSS (TTL-cached) ---
    stats = await ingest_feeds()
    stream = _load_stream()
    items = stream.get("items") or []

    rss_pool = _tap_unconsumed(items, _PACK_SIZE + 4, lane)
    if len(rss_pool) < _PACK_SIZE:
        more = _tap_unconsumed(items, _PACK_SIZE + 4, None)
        seen_ids = {r["id"] for r in rss_pool}
        for m in more:
            if m["id"] not in seen_ids:
                rss_pool.append(m)
                seen_ids.add(m["id"])

    # --- X search (paid; hard gated) ---
    x_hits: list[dict[str, Any]] = []
    x_err: str | None = None
    x_skipped: str | None = None
    force_x_mode = mode in ("x", "x-search")
    rss_thin = len(rss_pool) < _PACK_SIZE

    from services import x_search

    if settings.DRY_RUN:
        x_skipped = "dry_run"
    elif not x_search.search_enabled():
        x_skipped = "x_search_disabled"
    elif force_x_mode or rss_thin:
        try:
            x_hits = x_search.pick_top_stories(lane, n=_X_SLOTS + 1)
        except Exception as e:
            x_err = str(e)
            x_hits = []
    else:
        x_skipped = "rss_sufficient"
        log.info(
            "X search skipped (RSS has %s items, pack=%s)",
            len(rss_pool),
            _PACK_SIZE,
        )

    recycled = False
    if not rss_pool and not x_hits:
        recycled_pool = [i for i in items if i.get("consumed_at")]
        recycled_pool = [
            i for i in recycled_pool if (i.get("lane") or "") == lane
        ] or recycled_pool
        recycled_pool.sort(key=lambda x: x.get("consumed_at") or "")
        rss_pool = recycled_pool[:_PACK_SIZE]
        recycled = bool(rss_pool)
        for c in rss_pool:
            c["consumed_at"] = None
            c["consumed_by_run"] = None

    pack = _build_wire_pack(x_hits, rss_pool, _PACK_SIZE)

    if pack:
        _mark_consumed(pack, rid)
        lines = [_pack_line(c) for c in pack]
        sources = sorted({c.get("source") for c in pack if c.get("source")})
        has_x = any(c.get("source") == "x-search" for c in pack)
        has_rss = any(c.get("source") != "x-search" for c in pack)
        if has_x and has_rss:
            src = "x+rss"
        elif has_x:
            src = "x-search"
        elif recycled:
            src = "news-stream-recycle"
        else:
            src = "news-stream"

        primary = pack[0]
        tap_meta: dict[str, Any] = {
            "tap_size": len(pack),
            "pack_size": _PACK_SIZE,
            "item_ids": [c.get("id") for c in pack if c.get("id")],
            "sources": sources,
            "lanes": sorted({c.get("lane") for c in pack if c.get("lane")}),
            "fresh": not recycled,
            "recycled": recycled,
            "lane": lane,
            "style_id": style_id,
            "primary_title": primary.get("title") or primary.get("line"),
            "primary_source": primary.get("source"),
            "headlines": [
                {
                    "title": c.get("title"),
                    "source": c.get("source"),
                    "url": c.get("url") or c.get("link"),
                }
                for c in pack
            ],
            "ingest": stats,
            "stream": stream_stats(),
        }
        if has_x:
            x_item = next(c for c in pack if c.get("source") == "x-search")
            tap_meta["x_post_url"] = x_item.get("url")
            tap_meta["x_score"] = x_item.get("score")
            tap_meta["x_likes"] = x_item.get("likes")
        if x_err:
            tap_meta["x_search_error"] = x_err
        if x_skipped:
            tap_meta["x_search_skipped"] = x_skipped
        return format_bullets(lines), src, tap_meta

    return (
        format_bullets(
            [
                "Global markets and power systems shift under pressure from competing headlines",
            ]
        ),
        "fallback-static",
        {"fresh": False, "lane": lane, "style_id": style_id, "tap_size": 1},
    )
