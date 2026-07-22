"""Grok steps: art director + caption + Generative Stream slug (Session 2)."""

from __future__ import annotations

import httpx

from config import settings
from services.xai_client import client

ART_DIRECTOR_SYSTEM = """You are art director for "Planet Hack" (@tunastarlink).
3D digital CGI, one hero, real negative space — do not overcrowd.

Output ONLY this structure (no markdown fences):

CAMERA: <one line>
HERO: <one line — single subject>
CHAOS: <one line — ONE metaphor for the single news story>
PALETTE: <limited; name 2–3 colors + void>
MOOD: <3–6 words>
DETAIL: <1–2 sentences max; keep air in the frame>

Rules:
- Metaphor only from the ONE story. No politicians, flags, logos, headlines, maps.
- Match the shot type notes. Prefer calm power over scrapyard chaos unless style is Data Tunnel.
- No readable text in the image.
"""

CAPTION_SYSTEM = (
    "Caption for Planet Hack digital art. "
    "1–2 short atmospheric sentences about the place in the image. "
    "Max ~180 characters. No hashtags (we append them). No URLs. No newlines. "
    "Do not name politicians or paste the news headline. Mood only."
)

STREAM_SLUG_SYSTEM = (
    "Write one short sentence for an X reply. "
    "It must summarize the single news story in plain words (no hashtag). "
    "Max 160 characters. No URLs. No hashtags. Neutral tone."
)


async def craft_art_brief(events: str, style: dict) -> str:
    if settings.DRY_RUN:
        return (
            f"CAMERA: wide 16:9, {style.get('label')}\n"
            f"HERO: single digital form matching style\n"
            f"CHAOS: one quiet metaphor for the story\n"
            f"PALETTE: void + cyan + one accent\n"
            f"MOOD: focused, atmospheric\n"
            f"DETAIL: Negative space; do not fill the frame."
        )

    user = f"""Shot type: {style.get('label')} — {style.get('description')}

Shot notes:
{style.get('art_director_notes')}

SINGLE news story to metaphorize (do NOT paint text/headlines):
{events}

Fill CAMERA/HERO/CHAOS/PALETTE/MOOD/DETAIL now."""

    if settings.EDGE_TEXT == "lemonade":
        return await _lemonade_chat(ART_DIRECTOR_SYSTEM, user, max_tokens=280)
    return await _xai_chat(ART_DIRECTOR_SYSTEM, user, max_tokens=280, temperature=0.65)


async def craft_caption(events: str, style_label: str, art_brief: str = "") -> str:
    """Caption body only — hashtags applied in x_publish."""
    if settings.DRY_RUN:
        return f"Inside the {style_label} layer, one signal holds the dark open."

    user = (
        f"Style: {style_label}\n"
        f"Art brief:\n{art_brief[:400]}\n"
        f"Story mood (do not quote):\n{events[:200]}\n\n"
        "Write the caption body only."
    )
    if settings.EDGE_TEXT == "lemonade":
        return await _lemonade_chat(CAPTION_SYSTEM, user, max_tokens=100)
    return await _xai_chat(CAPTION_SYSTEM, user, max_tokens=100, temperature=0.7)


async def craft_stream_slug(events: str) -> str:
    """Short human sentence for Generative Stream reply (no hashtags)."""
    if settings.DRY_RUN:
        return "A single wire story, remixed as digital weather."

    # Prefer first bullet title
    first = ""
    for line in (events or "").splitlines():
        line = line.strip().lstrip("-• ").strip()
        if line:
            first = line.split(" — ")[0].strip()
            break
    if settings.DRY_RUN:
        return first[:160] if first else "A single wire story."

    user = f"News story:\n{events[:400]}\n\nOne short sentence summary for the reply body."
    if settings.EDGE_TEXT == "lemonade":
        text = await _lemonade_chat(STREAM_SLUG_SYSTEM, user, max_tokens=80)
    else:
        text = await _xai_chat(STREAM_SLUG_SYSTEM, user, max_tokens=80, temperature=0.5)
    text = (text or first or "A single story from the live wire.").strip()
    # strip accidental hashtags
    import re

    text = re.sub(r"#\w+", "", text).strip()
    return text[:180]


async def _xai_chat(
    system: str, user: str, max_tokens: int, temperature: float
) -> str:
    c = client()
    resp = c.chat.completions.create(
        model=settings.XAI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()


async def _lemonade_chat(system: str, user: str, max_tokens: int) -> str:
    url = f"{settings.LEMONADE_URL.rstrip('/')}/api/v1/chat/completions"
    payload = {
        "model": settings.LEMONADE_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user + "\n\n/no_think"},
        ],
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=60.0) as http:
        r = await http.post(url, json=payload)
        r.raise_for_status()
        body = r.json()
    msg = body["choices"][0]["message"]
    content = (msg.get("content") or "").strip()
    if not content:
        content = (msg.get("reasoning_content") or "").strip()[-400:]
    return content
