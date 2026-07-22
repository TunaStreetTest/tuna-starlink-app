"""World events for Planet Hack — prefer live RSS so we never paint from a model refusal."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Iterable

import httpx

from config import settings

# Free public feeds — no API key. Swap freely.
_RSS_FEEDS = (
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
)

_REFUSAL_PATTERNS = re.compile(
    r"(no access to real[- ]time|training data prior|as an ai|i (don't|do not) have|"
    r"cannot (provide|access) (live|real[- ]time)|knowledge cutoff|"
    r"current knowledge limited|i'm unable to browse)",
    re.I,
)


def events_look_like_refusal(text: str) -> bool:
    if not text or len(text.strip()) < 20:
        return True
    return bool(_REFUSAL_PATTERNS.search(text))


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _text(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return " ".join(el.text.split())


def _parse_rss(xml_bytes: bytes, limit: int) -> list[str]:
    root = ET.fromstring(xml_bytes)
    items: list[str] = []
    for el in root.iter():
        if _local(el.tag) != "item":
            continue
        title = ""
        desc = ""
        for child in el:
            name = _local(child.tag)
            if name == "title":
                title = _text(child)
            elif name in ("description", "summary"):
                desc = _text(child)
        # strip crude HTML from description
        desc = re.sub(r"<[^>]+>", " ", desc)
        desc = " ".join(desc.split())
        line = title
        if desc and desc.lower() not in title.lower():
            # keep short context only
            snippet = desc[:140].rstrip()
            if snippet:
                line = f"{title} — {snippet}"
        if line:
            items.append(line)
        if len(items) >= limit:
            break
    return items


async def fetch_rss_headlines(limit: int = 7) -> list[str]:
    headlines: list[str] = []
    async with httpx.AsyncClient(
        timeout=12.0,
        follow_redirects=True,
        headers={"User-Agent": "tuna-starlink-app/0.1 (PlanetHack events)"},
    ) as http:
        for url in _RSS_FEEDS:
            if len(headlines) >= limit:
                break
            try:
                r = await http.get(url)
                r.raise_for_status()
                batch = _parse_rss(r.content, limit=limit)
                for h in batch:
                    if h not in headlines:
                        headlines.append(h)
                    if len(headlines) >= limit:
                        break
            except Exception:
                continue
    return headlines[:limit]


def format_bullets(lines: Iterable[str]) -> str:
    return "\n".join(f"- {line}" for line in lines)


async def get_events() -> tuple[str, str]:
    """Return (events_text, source) where source is rss|xai|dry-run|fallback."""
    if settings.DRY_RUN:
        return (
            format_bullets(
                [
                    "Dry-run: global summit debates climate pledges",
                    "Dry-run: markets react to new chip export rules",
                    "Dry-run: athletes rewrite a world record overnight",
                    "Dry-run: coastal cities brace for a rare storm system",
                    "Dry-run: scientists publish a surprising deep-space signal paper",
                ]
            ),
            "dry-run",
        )

    mode = (settings.EVENTS_SOURCE or "rss").lower().strip()

    if mode in ("rss", "hybrid"):
        headlines = await fetch_rss_headlines(limit=7)
        if headlines:
            return format_bullets(headlines), "rss"

    if mode in ("xai", "hybrid"):
        # Lazy import avoids circular import at module load
        from services import xai_chat

        text = await xai_chat.summarize_events_llm()
        if not events_look_like_refusal(text):
            return text, "xai"

    # Last resort: fixed abstract seeds so Imagine still gets *something* real-shaped
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
    )
