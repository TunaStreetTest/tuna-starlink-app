"""Grok steps: art director brief + caption. Events come from services.events (RSS)."""

from __future__ import annotations

import httpx

from config import settings
from services.xai_client import client

EVENTS_SYSTEM = (
    "You are a concise news desk with up-to-date knowledge. "
    "Summarize the top world events factually and neutrally. Bullet list only."
)

EVENTS_USER = (
    "List the top 5–7 most important world news stories from the last 24 hours. "
    "Factual, neutral, one short bullet per story. No intro. "
    "If you truly cannot access current news, reply with exactly: EVENTS_UNAVAILABLE"
)

ART_DIRECTOR_SYSTEM = """You are art director for "Planet Hack" (@tunastarlink).
Hacker-movie 3D CGI: inside the computer, hacking the planet. Voxels, neon, debris.

Output ONLY this exact structure (no markdown fences, no extra sections):

CAMERA: <one line — angle, FOV, where we stand>
HERO: <one line — main subject>
CHAOS: <one line — what is breaking / infiltrating / storming — metaphor for the events>
PALETTE: <cyan + magenta + acid-green + void black + optional gold; give weights>
MOOD: <3–6 words>
DETAIL: <2 sentences max of extra geometry; dense; still image>

Rules:
- Abstract metaphors for events only. Never politicians, flags, logos, headlines, real maps.
- Fight stock look: broken geometry, debris in foreground, NOT clean perfect rings, NOT blue-only globe poster.
- No readable text in the scene description as on-image content.
"""

CAPTION_SYSTEM = (
    "You write the main social post caption for a digital art series called Planet Hack "
    "(hacker-movie 3D cyberspace / planetary mainframe). "
    "Write 2 short sentences, atmospheric and slightly literary. "
    "Hard max ~220 characters BEFORE the hashtag (we append #PlanetHack). "
    "Do NOT include hashtags yourself. No URLs. No newlines. "
    "No bullet lists. No news recap or headlines. "
    "Do not mention RSS, AI, prompts, or Grok. Speak as if the image is a real place we jacked into."
)


async def summarize_events_llm() -> str:
    """LLM-only events (used when EVENTS_SOURCE=xai or hybrid fallback)."""
    return await _xai_chat(EVENTS_SYSTEM, EVENTS_USER, max_tokens=500, temperature=0.3)


async def craft_art_brief(events: str, style: dict) -> str:
    """Grok art director: structured visual brief for Imagine."""
    if settings.DRY_RUN:
        return (
            f"CAMERA: deep inside spherical core, low Dutch angle, extreme FOV\n"
            f"HERO: half-dissolved data-Earth over a white-hot root spike ({style.get('label')})\n"
            f"CHAOS: fractured rings shedding voxels; packet storms where channels die\n"
            f"PALETTE: void 50%, cyan 20%, magenta 15%, acid-green 10%, gold 5%\n"
            f"MOOD: infiltration climax, vast, dangerous\n"
            f"DETAIL: Foreground voxel debris and unreadable UI shards. Kinetic still, not a clean diagram."
        )

    user = f"""Shot type: {style.get('label')} — {style.get('description')}

Shot notes:
{style.get('art_director_notes')}

World events to metaphorize (do NOT put these words in the image):
{events}

Fill the CAMERA/HERO/CHAOS/PALETTE/MOOD/DETAIL structure now."""

    if settings.EDGE_TEXT == "lemonade":
        return await _lemonade_chat(ART_DIRECTOR_SYSTEM, user, max_tokens=350)

    return await _xai_chat(ART_DIRECTOR_SYSTEM, user, max_tokens=350, temperature=0.7)


async def craft_caption(events: str, style_label: str, art_brief: str = "") -> str:
    if settings.DRY_RUN:
        return (
            f"Deep in the {style_label} layer, the conduit burns open and the machine "
            f"remembers we are still inside it. Pixel weather rolls through the dark; "
            f"the root node waits like a locked door that already knows our name. #PlanetHack"
        )

    user = (
        f"Style shot: {style_label}\n"
        f"Visual vibe from art director:\n{art_brief[:500]}\n"
        f"World context (mood only — do not name events):\n{events[:300]}\n\n"
        "Write the wordy main-post caption now. End with #PlanetHack only."
    )
    if settings.EDGE_TEXT == "lemonade":
        return await _lemonade_chat(CAPTION_SYSTEM, user, max_tokens=160)

    return await _xai_chat(CAPTION_SYSTEM, user, max_tokens=160, temperature=0.75)


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
