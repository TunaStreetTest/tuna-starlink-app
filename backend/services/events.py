"""Lean cool-tech wire for Planet Hack — SpaceX / Tesla / xAI / NVIDIA / AI only.

Cost rules:
  - RSS only by default (free). X Recent Search is opt-in + gated (see x_search).
  - Tiny focused feed set (few posts/day — not a news desk).
  - Ingest is TTL-cached; items expire by publish age so we never post week-old wire.
  - Single-story pack; ALWAYS prefer newest unconsumed story (never oldest).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote_plus

import httpx

from config import settings
from services import art_store

log = logging.getLogger("tuna-starlink.events")

# Topic-scoped free RSS. Prefer Google News queries over general world desks.
def _gnews(query: str) -> str:
    # Short window only — few posts/day; never stockpile two weeks of wire.
    q = f"{query} when:3d"
    return (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(q)}&hl=en-US&gl=US&ceid=US:en"
    )


# Dialed-back source set (3 feeds). Hard-focused on the brands we post about.
_RSS_FEEDS: tuple[tuple[str, str, str], ...] = (
    # source_id, url, default_lane
    ("gnews-spacex", _gnews("SpaceX OR Starship OR Starlink OR Falcon"), "space"),
    ("gnews-tesla-xai", _gnews("Tesla OR Optimus OR xAI OR Grok OR Dojo"), "ai"),
    ("gnews-nvidia-ai", _gnews("NVIDIA OR Blackwell OR OpenAI OR Anthropic OR LLM"), "gpu"),
)

# Style lanes → cool tech only (no geopolitics / markets / climate desks).
_LANE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "space": (
        "spacex", "starship", "starlink", "falcon", "crew dragon", "super heavy",
        "orbital", "launch", "rocket", "satellite constellation", "mars", "iss",
        "raptor", "dragon capsule",
    ),
    "gpu": (
        "nvidia", "gpu", "h100", "h200", "b100", "b200", "blackwell", "hopper",
        "cuda", "tensor core", "ai chip", "accelerator", "semiconductor",
        "tpu", "inference chip", "gb200", "rubin",
    ),
    "ai": (
        "openai", "anthropic", "claude", "chatgpt", "gpt", "gemini", "grok",
        "llm", "large language", "model release", "open weights", "checkpoint",
        "mistral", "llama", "deepmind", "xai", "foundation model",
        "tesla", "optimus", "dojo", "fsd", "full self-driving", "robotaxi",
    ),
    # legacy aliases still accepted from older styles / configs
    "tech": (
        "ai ", "gpu", "nvidia", "openai", "spacex", "tesla", "xai", "grok",
        "chip", "model", "llm", "starlink",
    ),
    "science": (
        "spacex", "starship", "starlink", "orbital", "satellite", "rocket",
    ),
    "geopolitics": (),  # empty — never prefer political lane
    "markets": (
        "nvidia", "gpu", "ai chip", "semiconductor", "datacenter", "tesla",
    ),
}

# Must match at least one — keeps camels / elections / lifestyle out.
_COOL_TECH_RE = re.compile(
    r"\b("
    r"spacex|starship|starlink|falcon\s*9|crew\s*dragon|super\s*heavy|"
    r"tesla|optimus|dojo|robotaxi|full self[- ]?driving|\bfsd\b|"
    r"nvidia|gpu|gpus|h100|h200|b100|b200|blackwell|hopper|cuda|tensor\s*core|gb200|"
    r"openai|anthropic|claude|chatgpt|gpt-?\d|gemini|grok|llm|llms|"
    r"large language|foundation model|model (release|launch|weights|checkpoint)|"
    r"open[- ]?weights|inference|deepmind|mistral|llama|meta ai|xai|\bx\.?ai\b|"
    r"ai chip|accelerator|semiconductor|datacenter|data center|tpu|"
    r"rocket launch|orbital|satellite constellation"
    r")\b",
    re.I,
)

_BLOCK_RE = re.compile(
    r"\b("
    r"camel|camels|election|senate|congress|democrat|republican|gop\b|"
    r"gaza|hamas|ukraine|israel|war crime|bombing|airstrike|"
    r"murder|homicide|celebrity|reality tv|football|nba|nfl|cricket|"
    r"recipe|diet|pregnant|divorce|soap opera|immigration raid|"
    r"tariff bill|stock market crash|fed rate|"
    r"copyright settlement|copyright lawsuit|authors have mixed"  # dull legal recycle
    r")\b",
    re.I,
)

# Soft secondary features — real articles, wrong signal for a tech wire post body.
# "Space photo of the day" titles misled caption expansion ("floating" → "in orbit").
_SOFT_FEATURE_RE = re.compile(
    r"("
    r"photo of the day|picture of the day|image of the day|"
    r"space photo of the day|looks absolutely|stunning photos?|"
    r"don'?t miss these|you may like"
    r")",
    re.I,
)

_STREAM_NAME = ".news_stream.json"
# Bump wipes old 14-day / Ars / stale Anthropic-settlement cache on next load.
_STREAM_SCHEMA = "cool-tech-v2"
_STREAM_MAX_ITEMS = 18  # few posts/day — tiny working set
_ITEMS_PER_FEED = 5
_PACK_SIZE = 1  # single story only — full text drives stream + image
_X_SLOTS = 1
_X_MIN_SCORE = 40
# Drop anything older than this (publish time, else ingest time). Never post week-old wire.
_MAX_STORY_AGE_HOURS = 72


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


def _parse_published(raw: str | None) -> datetime | None:
    """Best-effort RSS pubDate / ISO → aware UTC datetime."""
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip()
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError, OverflowError):
        pass
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _item_when(item: dict[str, Any]) -> datetime | None:
    """Story time: prefer publisher clock, else when we first saw it."""
    for key in ("published_at", "published", "ingested_at"):
        raw = item.get(key)
        if not raw:
            continue
        if key == "published_at" or key == "ingested_at" or (
            isinstance(raw, str) and "T" in raw
        ):
            try:
                dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                pass
        dt = _parse_published(str(raw))
        if dt:
            return dt
    return None


def _age_hours(item: dict[str, Any]) -> float | None:
    when = _item_when(item)
    if when is None:
        return None
    return (datetime.now(timezone.utc) - when).total_seconds() / 3600.0


def _freshness_key(item: dict[str, Any]) -> str:
    """Sort key: newest publish/ingest first (ISO strings sort lexicographically)."""
    when = _item_when(item)
    if when is not None:
        return when.isoformat()
    return item.get("ingested_at") or item.get("published_at") or ""


def _is_fresh(item: dict[str, Any], max_age_hours: float = _MAX_STORY_AGE_HOURS) -> bool:
    age = _age_hours(item)
    if age is None:
        # Unknown age: keep briefly via ingest stamp only if present and young-ish
        return True
    return age <= max_age_hours


def _is_cool_tech(title: str, summary: str = "") -> bool:
    """Hard gate: SpaceX / Tesla / xAI / NVIDIA / AI model universe only."""
    blob = f"{title} {summary}"
    if _BLOCK_RE.search(blob):
        return False
    return bool(_COOL_TECH_RE.search(blob))


def _infer_lane(title: str, summary: str, default: str) -> str:
    blob = f"{title} {summary}".lower()
    scores = {lane: 0 for lane in _LANE_KEYWORDS if _LANE_KEYWORDS[lane]}
    for lane, kws in _LANE_KEYWORDS.items():
        if not kws:
            continue
        for kw in kws:
            if kw in blob:
                scores[lane] = scores.get(lane, 0) + 1
    if not scores:
        return default
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return default
    # Map legacy aliases to primary cool lanes
    if best in ("tech",):
        return "ai"
    if best in ("science",):
        return "space"
    if best in ("markets",):
        return "gpu"
    if best == "geopolitics":
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
        # Drop politics / lifestyle / off-theme noise before it hits the stream
        if not _is_cool_tech(title, desc):
            continue
        # Soft features mislead the caption (photo-of-the-day "floating" ≠ orbital news)
        if _SOFT_FEATURE_RE.search(f"{title} {desc}"):
            continue
        # Reject stub titles ("SpaceX - SpaceX") and ultra-thin blurbs
        if len(title) < 28 or title.count(" ") < 4:
            continue
        # Title + summary only as source material — never invent beyond this text.
        line = title
        if desc and desc.lower() not in title.lower():
            snippet = desc[:420].rstrip()
            if snippet:
                line = f"{title} — {snippet}"
        lane = _infer_lane(title, desc, default_lane)
        pub_dt = _parse_published(pub)
        # Skip already-stale headlines at the door (Google sometimes still surfaces them)
        if pub_dt is not None:
            age_h = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600.0
            if age_h > _MAX_STORY_AGE_HOURS:
                continue
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
                "published_at": pub_dt.isoformat() if pub_dt else None,
                "ingested_at": _now(),
                "consumed_at": None,
                "consumed_by_run": None,
            }
        )
        if len(items) >= limit:
            break
    # Newest first within this feed batch
    items.sort(key=_freshness_key, reverse=True)
    return items


def _load_stream() -> dict[str, Any]:
    path = _stream_path()
    if not path.is_file():
        return {"items": [], "updated_at": None, "taps": 0, "schema": _STREAM_SCHEMA}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"items": [], "updated_at": None, "taps": 0, "schema": _STREAM_SCHEMA}
        # Schema bump: discard old BBC world/camel/politics cache
        if data.get("schema") != _STREAM_SCHEMA:
            log.info(
                "news stream schema %r → %r; resetting cache",
                data.get("schema"),
                _STREAM_SCHEMA,
            )
            return {"items": [], "updated_at": None, "taps": 0, "schema": _STREAM_SCHEMA}
        data.setdefault("items", [])
        data.setdefault("taps", 0)
        data["schema"] = _STREAM_SCHEMA
        return data
    except (json.JSONDecodeError, OSError):
        return {"items": [], "updated_at": None, "taps": 0, "schema": _STREAM_SCHEMA}


def _save_stream(data: dict[str, Any]) -> None:
    import os

    path = _stream_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["schema"] = _STREAM_SCHEMA
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


def _prune_stale(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop stories older than max age. Prefer published_at; never hoard week-old wire."""
    kept: list[dict[str, Any]] = []
    dropped = 0
    for i in items:
        # Normalize published_at if we only have raw RSS pubDate
        if not i.get("published_at") and i.get("published"):
            dt = _parse_published(str(i.get("published")))
            if dt:
                i["published_at"] = dt.isoformat()
        if _is_fresh(i):
            kept.append(i)
        else:
            dropped += 1
    if dropped:
        log.info("pruned %s stale stories (>%sh)", dropped, _MAX_STORY_AGE_HOURS)
    return kept


def _trim_stream(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = _prune_stale(items)
    if len(items) <= _STREAM_MAX_ITEMS:
        # Still sort newest-first for a stable file / UI
        items.sort(key=_freshness_key, reverse=True)
        return items
    unconsumed = [i for i in items if not i.get("consumed_at")]
    consumed = [i for i in items if i.get("consumed_at")]
    # Newest stories first — never keep the oldest just because they sat unconsumed
    unconsumed.sort(key=_freshness_key, reverse=True)
    consumed.sort(key=_freshness_key, reverse=True)
    keep = unconsumed[:_STREAM_MAX_ITEMS]
    if len(keep) < _STREAM_MAX_ITEMS:
        keep.extend(consumed[: _STREAM_MAX_ITEMS - len(keep)])
    keep.sort(key=_freshness_key, reverse=True)
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
                        prev = by_id[item["id"]]
                        if not prev.get("lane"):
                            prev["lane"] = item["lane"]
                        # Refresh publish clock if we learn it later
                        if item.get("published_at") and not prev.get("published_at"):
                            prev["published_at"] = item["published_at"]
                            prev["published"] = item.get("published") or prev.get("published")
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
    """Pick newest unconsumed stories (by publish time). Never oldest-first."""
    free = [i for i in items if not i.get("consumed_at") and _is_fresh(i)]
    if lane:
        lane_free = [i for i in free if (i.get("lane") or "") == lane]
        # Only stay in-lane when that lane still has fresh stories
        if lane_free:
            free = lane_free
    free.sort(key=_freshness_key, reverse=True)
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
    fresh_unconsumed = 0
    newest_pub: str | None = None
    for i in items:
        if i.get("consumed_at"):
            continue
        if not _is_fresh(i):
            continue
        fresh_unconsumed += 1
        lane = i.get("lane") or "unknown"
        by_lane[lane] = by_lane.get(lane, 0) + 1
        fk = _freshness_key(i)
        if fk and (newest_pub is None or fk > newest_pub):
            newest_pub = fk
    return {
        "total": len(items),
        "unconsumed": sum(1 for i in items if not i.get("consumed_at")),
        "fresh_unconsumed": fresh_unconsumed,
        "consumed": sum(1 for i in items if i.get("consumed_at")),
        "taps": stream.get("taps") or 0,
        "updated_at": stream.get("updated_at"),
        "newest_story_at": newest_pub,
        "max_story_age_hours": _MAX_STORY_AGE_HOURS,
        "unconsumed_by_lane": by_lane,
        "path": str(_stream_path()),
        "pack_size": _PACK_SIZE,
        "tap_size": _PACK_SIZE,
        "feeds": [f[0] for f in _RSS_FEEDS],
        "feeds_count": len(_RSS_FEEDS),
        "rss_ttl_minutes": int(settings.RSS_INGEST_TTL_MINUTES or 0),
        "x_search_enabled": bool(settings.X_SEARCH_ENABLED),
        "schema": stream.get("schema"),
    }


def _dedupe_key(text: str) -> str:
    return re.sub(r"\W+", "", (text or "")[:56].lower())


def _pack_line(item: dict[str, Any]) -> str:
    """Single-story source text: title + summary only (caption will not invent past this)."""
    title = (item.get("title") or "").strip()
    summary = re.sub(r"https?://\S+", "", (item.get("summary") or "").strip())
    summary = re.sub(r"\s+", " ", summary).strip()
    line = re.sub(r"https?://\S+", "", (item.get("line") or item.get("text") or "").strip())
    line = re.sub(r"\s+", " ", line).strip()

    # Prefer longest clean string that is still only wire text
    if title and summary and summary.lower() not in title.lower():
        body = f"{title} — {summary}"
    elif line and len(line) >= len(title):
        body = line
    elif title and line and title.lower() not in line.lower():
        body = f"{title} — {line}"
    else:
        body = line or title
    return body[:900]


# Core brands we post about — strong boost so dull edge stories lose to the real wire.
_PRIMARY_BOOST = re.compile(
    r"\b(spacex|starship|starlink|falcon|tesla|optimus|dojo|xai|grok|"
    r"nvidia|blackwell|h100|b200|gb200|cuda|"
    r"openai|anthropic|claude|chatgpt|gpt|llm|model release|launch|"
    r"inference|open.?weights)\b",
    re.I,
)


def _primary_rank(item: dict[str, Any]) -> int:
    """Higher = better primary. Official X beats secondary RSS rewrites."""
    title = item.get("title") or item.get("line") or ""
    score = int(item.get("score") or 0)
    is_x = item.get("source") == "x-search"
    is_primary_acct = bool(item.get("primary_account"))
    # Prefer primary brand posts from X over Google News rewrites
    if is_x:
        score += 80
        if is_primary_acct:
            score += 50
    if _PRIMARY_BOOST.search(title):
        score += 25
    if _SOFT_FEATURE_RE.search(title):
        score -= 80
    # Official account posts are already cool-tech by construction — don't
    # punish short "still afloat…" SpaceX updates for omitting the brand name.
    if not is_primary_acct and not _is_cool_tech(
        title, item.get("summary") or item.get("line") or ""
    ):
        score -= 100
    n = len(title)
    if 40 <= n <= 140:
        score += 10
    elif n > 180:
        score -= 8

    # Freshness still matters — few posts/day → newest story
    age = _age_hours(item)
    if age is None:
        if is_x:
            score += 30
        else:
            score -= 5
    elif age <= 6:
        score += 50
    elif age <= 24:
        score += 35
    elif age <= 48:
        score += 15
    elif age <= _MAX_STORY_AGE_HOURS:
        score += 0
    else:
        score -= 80
    return score


def _build_wire_pack(
    x_hits: list[dict[str, Any]],
    rss_hits: list[dict[str, Any]],
    pack_size: int = _PACK_SIZE,
) -> list[dict[str, Any]]:
    """Merge X primary + RSS; rank so official posts win over soft RSS."""
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
                "primary_account": bool(h.get("primary_account")),
                "published_at": h.get("created_at") or h.get("published_at"),
            }
        )
        x_kept += 1

    for h in rss_hits:
        if len(candidates) >= pack_size + 2:
            break
        title = h.get("title") or h.get("line") or ""
        if _SOFT_FEATURE_RE.search(title):
            continue
        key = _dedupe_key(title)
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
                "published_at": h.get("published_at"),
                "published": h.get("published"),
                "ingested_at": h.get("ingested_at"),
            }
        )

    # Rank by primary trust + freshness; tie-break newest publish time
    candidates.sort(
        key=lambda c: (_primary_rank(c), _freshness_key(c)),
        reverse=True,
    )
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
            f"Dry-run {stamp}: SpaceX Starship stacks for next orbital flight test "
            "while NVIDIA ships next-gen AI GPUs and labs drop open-weight models."
        ]
        return (
            format_bullets(lines),
            "dry-run-stream",
            {"tap_size": len(lines), "fresh": True, "lane": lane, "style_id": style_id},
        )

    rid = run_id or f"tap-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    # Map style lanes → cool-tech lanes
    lane_raw = (lane or "ai").lower().strip()
    lane_map = {
        "geopolitics": "space",
        "science": "space",
        "tech": "ai",
        "markets": "gpu",
    }
    lane = lane_map.get(lane_raw, lane_raw)
    mode = (settings.EVENTS_SOURCE or "stream").lower().strip()

    # --- lean RSS (TTL-cached; force refresh if nothing fresh left) ---
    stats = await ingest_feeds()
    stream = _load_stream()
    items = stream.get("items") or []
    # Drop stale rows even when ingest was cache-skipped
    pruned = _prune_stale(items)
    if len(pruned) != len(items):
        stream["items"] = _trim_stream(pruned)
        _save_stream(stream)
        items = stream["items"]

    rss_pool = _tap_unconsumed(items, _PACK_SIZE + 4, lane)
    if len(rss_pool) < _PACK_SIZE:
        more = _tap_unconsumed(items, _PACK_SIZE + 4, None)
        seen_ids = {r["id"] for r in rss_pool}
        for m in more:
            if m["id"] not in seen_ids:
                rss_pool.append(m)
                seen_ids.add(m["id"])

    # Cache hit but no fresh stories → re-hit feeds once (don't post week-old wire)
    if len(rss_pool) < _PACK_SIZE and stats.get("cached"):
        log.info("no fresh unconsumed stories; forcing RSS re-ingest")
        stats = await ingest_feeds(force=True)
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

    # --- X search (paid; hard gated). Prefer primary brand posts over RSS rewrites. ---
    x_hits: list[dict[str, Any]] = []
    x_err: str | None = None
    x_skipped: str | None = None
    force_x_mode = mode in ("x", "x-search")

    from services import x_search

    if settings.DRY_RUN:
        x_skipped = "dry_run"
    elif not x_search.search_enabled():
        x_skipped = "x_search_disabled"
    else:
        # Always consult X when enabled — official SpaceX/Tesla/NVIDIA/xAI posts
        # beat "photo of the day" Google News titles even when RSS is full.
        try:
            x_hits = x_search.pick_top_stories(lane, n=_X_SLOTS + 1)
            if not x_hits and force_x_mode:
                log.info("X search empty in force-x mode lane=%s", lane)
        except Exception as e:
            x_err = str(e)
            x_hits = []

    recycled = False
    if not rss_pool and not x_hits:
        # Only recycle still-fresh stories; newest first (never oldest consumed)
        recycled_pool = [
            i for i in items if i.get("consumed_at") and _is_fresh(i)
        ]
        lane_recycled = [
            i for i in recycled_pool if (i.get("lane") or "") == lane
        ]
        recycled_pool = lane_recycled or recycled_pool
        recycled_pool.sort(key=_freshness_key, reverse=True)
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
                "NVIDIA AI GPUs and open-weight LLMs reshape the compute stack "
                "while SpaceX pads stack the next Starship flight — pure tech wire.",
            ]
        ),
        "fallback-static",
        {"fresh": False, "lane": lane, "style_id": style_id, "tap_size": 1},
    )
