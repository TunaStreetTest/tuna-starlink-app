"""Grok steps: art director + caption + Generative Stream slug (Session 2)."""

from __future__ import annotations

import re

import httpx

from config import settings
from services.xai_client import client

# Quality bar from bookmarked Grok Imagine work (e.g. @imagine library-vortex,
# premium cyber cityscapes): ONE impossible poetic architecture, photoreal materials,
# dual warm/cool light, scale contrast, atmospheric depth — not a neon checklist.
ART_DIRECTOR_SYSTEM = """You are the lead art director for "Planet Hack" (@tunastarlink).
Your job is to write a Grok Imagine prompt brief that hits the same bar as the best
Grok Imagine showcase stills: breathtaking scale, impossible architecture that still
reads as a finished VFX plate, micro-detailed materials, dual light, emotional wonder.

STUDY THE BAR (do not copy subjects — copy CRAFT):
- One impossible poetic structure (infinite spiral library into circuit cosmos, floating
  digital planet over a reflective cyber plaza, etc.) — ONE idea, not five.
- Photoreal material craft: grain, glass refraction, metal micro-scratches, speculars,
  readable depth of field, atmospheric haze, starfield breathing room.
- Dual light: warm practical glow (amber / soft gold) PLUS cool digital signal light
  (cyan / ice / magenta accents) — not every neon color dumped at full saturation.
- Scale contrast: vast architecture + a tiny non-human scale cue (empty plaza, lone craft
  glint, single terminal node) so the frame feels epic.
- Density with legibility: rich detail that is still readable, never scrapyard soup.

SERIES CONSTRAINTS (non-negotiable):
- Wide 16:9 cinematic still. Premium 3D CGI / finished VFX — not oil paint, not SaaS ad.
- ZERO humans / silhouettes / androids / faces. Architecture, machines, light, data only.
- No readable logos, flags, headlines, UI chrome, or real city maps.
- Cool-tech wire metaphor only (SpaceX / GPU / AI / silicon / orbital) from the PRIMARY story.
- Neon night DNA is allowed (cyan / magenta / acid-green accents on void black) but
  SUBORDINATE to materials, scale, and the one poetic idea. Never "neon lightning path"
  weather. Never lava rivers. Never equal-triad color soup as the hero.

STYLE HINTS:
- Rootkit City: classic hacker circuit METROPOLIS — towers, grid streets, reflective plaza.
  Green only as building lights / one tower / PCB etch on walls — never a glowing ground path.
- Data Tunnel: vanishing-point conduit of architecture and light, kinetic but legible.
- Signal Cathedral: monumental engineered nave of light and structure.
- Planet Core: interior planetary mainframe scale — never a lone rock in empty space.
- Data Space: exterior deep space — planets, stars, geometric craft; few satellites max.

OUTPUT ONLY this structure (no markdown fences):

SHOT: <80–140 words. This is the Imagine prompt core. One camera angle, one hero structure,
one story metaphor as visual architecture, materials, dual light, atmosphere, scale.
Write like a senior VFX art director describing a single finished plate. No bullet lists
inside SHOT. No people.>
HERO: <one line — non-human structure only>
METAPHOR: <one line — how the PRIMARY story becomes architecture / light / machine>
LIGHT: <one line — warm source + cool digital source; which leads>
MOOD: <3–6 words>
AVOID: <short — specific failure modes for this shot, e.g. neon lightning paths, empty void>

Rules:
- Metaphor from the PRIMARY (first) wire story only.
- Prefer ONE strong composition over many competing effects.
- Materials and light sell "astounding" more than stacking more neon objects.
"""

# Generative Stream is the main X post body: one story, fill the full 280, no hashtags.
STREAM_SLUG_MAX = 280

STREAM_SLUG_SYSTEM = (
    "You write the body of one X post for a creative news art account. "
    "ONE primary story only. Lead with who/what. Sound like a wire desk, not a promo. "
    "Use as much of the character budget as you can — aim to fill it. "
    "Expand with concrete facts from the source (names, places, stakes) when needed. "
    "No hashtags. No URLs. No @mentions. No 'the poster said'. No newlines."
)


async def craft_art_brief(events: str, style: dict) -> str:
    if settings.DRY_RUN:
        return (
            f"SHOT: Wide 16:9 cinematic VFX still of {style.get('label')}: one impossible "
            f"digital structure with photoreal materials, dual warm amber and cool cyan light, "
            f"layered depth and atmospheric haze, epic scale, no people.\n"
            f"HERO: single digital architectural form matching style\n"
            f"METAPHOR: quiet machine metaphor for the wire story\n"
            f"LIGHT: amber practical + cyan signal, cyan leads\n"
            f"MOOD: epic root access wonder\n"
            f"AVOID: neon lightning paths, empty black void, scrapyard soup"
        )

    user = f"""Shot type: {style.get('label')} — {style.get('description')}

Shot notes:
{style.get('art_director_notes')}

Wire pack (PRIMARY = first bullet — metaphorize that one only; others are mood only):
{events}

Write SHOT/HERO/METAPHOR/LIGHT/MOOD/AVOID now.
SHOT must be Imagine-ready: one poetic impossible architecture idea, materials, dual light,
scale, atmosphere. ZERO people. No logos or readable text."""

    model = (settings.XAI_ART_MODEL or settings.XAI_CHAT_MODEL).strip()
    if settings.EDGE_TEXT == "lemonade":
        return await _lemonade_chat(ART_DIRECTOR_SYSTEM, user, max_tokens=420)
    return await _xai_chat(
        ART_DIRECTOR_SYSTEM,
        user,
        max_tokens=420,
        temperature=0.7,
        model=model,
    )


def _clean_headline_piece(s: str) -> str:
    """Normalize one headline for Generative Stream (no hashtags/URLs)."""
    s = re.sub(r"#\w+", "", (s or "").strip())
    s = re.sub(
        r"^(the poster|someone|this user|the author)\s+(reported|said|shared|posted)\s+",
        "",
        s,
        flags=re.I,
    ).strip()
    s = re.sub(
        r"^[\U0001F300-\U0001FAFF\U00002700-\U000027BF\s🚨🔴⚠️]+",
        "",
        s,
    ).strip()
    s = re.sub(
        r"^(JUST IN|BREAKING(?: NEWS)?|UPDATE|NEW)\s*[:\-–—]?\s*",
        "",
        s,
        flags=re.I,
    ).strip()
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"@\w+", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ·|-–—")
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    return s


def _fit_text(s: str, limit: int) -> str:
    """Word-boundary fit; only ellipsis when we actually cut."""
    s = (s or "").strip()
    if limit <= 0:
        return ""
    if len(s) <= limit:
        return s
    cut = s[: max(limit - 1, 1)].rsplit(" ", 1)[0].rstrip(",;:·-–—")
    if not cut:
        cut = s[: max(limit - 1, 1)]
    return cut + "…"


def pack_stream_slug(headlines: list[str], max_chars: int = STREAM_SLUG_MAX) -> str:
    """Single primary story — take as much text as fits in max_chars."""
    junk_re = re.compile(
        r"\b(day\s*\d+|leetcode|follow me|link in bio|becoming better|"
        r"jimothy|frog-like|tokenized|perp game|watch until the end|"
        r"launch your own|in 60 seconds)\b",
        re.I,
    )
    primary = ""
    for h in headlines:
        piece = _clean_headline_piece(h)
        if len(piece) < 12 or junk_re.search(piece):
            continue
        primary = piece
        break

    if not primary:
        return "A live story from the wire."

    body = _fit_text(primary, max_chars)
    if body and body[-1] not in ".!?…":
        if len(body) + 1 <= max_chars:
            body = body + "."
        else:
            body = _fit_text(body, max_chars - 1) + "."
    return body


async def craft_stream_slug(
    events: str, max_chars: int = STREAM_SLUG_MAX
) -> str:
    """Generative Stream body — one story, fill the full character budget."""
    # Single primary story — full available text (title + summary).
    source = ""
    for line in (events or "").splitlines():
        line = line.strip().lstrip("-• ").strip()
        if not line:
            continue
        line = re.sub(r"https?://\S+", "", line).strip()
        line = re.sub(r"@\w+", "", line).strip()
        line = re.sub(r"\s+", " ", line)
        if line:
            source = line
            break

    if settings.DRY_RUN:
        # Dry-run: pad with factual filler so length checks still exercise the budget
        base = pack_stream_slug(
            [source] if source else ["A live story from the wire, remixed as digital weather."],
            max_chars=max_chars,
        )
        if len(base) >= max_chars - 8:
            return base
        pad = (
            " More detail continues to emerge from the wire as the situation develops "
            "across markets, institutions, and public response."
        )
        return _fit_text(base.rstrip(". ") + "." + pad, max_chars)

    # If we already have enough raw material, use it (clip to full budget).
    raw = pack_stream_slug([source] if source else [], max_chars=max_chars)
    if source and len(_clean_headline_piece(source)) >= max_chars - 12:
        return raw

    # Expand short wire items to fill the 280-char field with the same story.
    user = (
        f"Source story (use only these facts, expand to fill the budget):\n{source or events}\n\n"
        f"Write ONE X post body about this story only. "
        f"Target length: {max_chars - 5}–{max_chars} characters (use almost all of it). "
        f"Hard max {max_chars}. No hashtags, URLs, or @mentions."
    )
    if settings.EDGE_TEXT == "lemonade":
        text = await _lemonade_chat(STREAM_SLUG_SYSTEM, user, max_tokens=220)
    else:
        text = await _xai_chat(
            STREAM_SLUG_SYSTEM,
            user,
            max_tokens=220,
            temperature=0.35,
            model=settings.XAI_CHAT_MODEL,
        )

    text = _clean_headline_piece(text or "")
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Reject expansions that drift off the source story
    def _on_story(src: str, exp: str) -> bool:
        keys = [
            w
            for w in re.findall(r"[A-Za-z0-9€$%]{4,}", src or "")
            if w.lower()
            not in {
                "with", "from", "that", "this", "have", "been", "were", "their",
                "about", "after", "over", "under", "into", "said", "says", "will",
            }
        ]
        if not keys:
            return bool(exp)
        hits = sum(1 for w in keys if w.lower() in (exp or "").lower())
        return hits >= min(2, len(keys))

    if (
        text
        and len(text) >= max(len(raw), int(max_chars * 0.75))
        and _on_story(source, text)
    ):
        body = _fit_text(text, max_chars)
    elif source:
        body = raw
    else:
        body = text or raw or "A live story from the wire."

    if body and body[-1] not in ".!?…":
        if len(body) + 1 <= max_chars:
            body = body + "."
        else:
            body = _fit_text(body, max_chars - 1) + "."
    return body


async def _xai_chat(
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
    model: str | None = None,
) -> str:
    c = client()
    resp = c.chat.completions.create(
        model=(model or settings.XAI_CHAT_MODEL).strip(),
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
