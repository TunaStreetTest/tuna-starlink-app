"""Grok steps: art director brief + source-only stream caption.

Art director may metaphorize. The X caption must never invent facts past the wire text.
"""

from __future__ import annotations

import re

import httpx

from config import settings
from services.wire_quality import expand_handles
from services.xai_client import client

# Quality bar from bookmarked Grok Imagine work (e.g. @imagine library-vortex,
# premium cyber cityscapes): ONE impossible poetic architecture, photoreal materials,
# dual warm/cool light, scale contrast, atmospheric depth — not a neon checklist.
ART_DIRECTOR_SYSTEM = """You are the lead art director for "Planet Hack" (@tunastarlink).
Write a Grok Imagine brief that hits the same CRAFT bar as the best @imagine showcase
stills: one impossible poetic architecture, photoreal materials, dual light, wonder.

CRAFT (copy this, not the subjects):
- ONE idea. One camera. One hero structure. Breathing room around it.
- Photoreal materials: glass refraction, metal grain, silicon micro-etches, speculars,
  readable depth of field, atmospheric haze. Luminous — not a dark metal warehouse.
- Dual light: one warm practical (amber / soft gold) PLUS one cool digital (cyan / ice /
  magenta accent). Neon is subordinate, never the subject.
- Scale contrast: vast architecture + one tiny non-human cue (empty plaza, lone craft
  glint, single terminal node).

SERIES LOCK:
- Wide 16:9 finished VFX still. Zero humans / silhouettes / faces.
- No logos, flags, readable UI, lightning-bolt weather, lava, scrapyard soup.
- Metaphor the PRIMARY wire story only (SpaceX / GPU / AI / silicon / orbital).

STYLE (one hero, not a packed catalog):
- Rootkit City: a luminous digital city INSIDE the computer. One neon-etched megastructure
  or canyon as the hero — glass-silicon facades, cyan streets, magenta nodes, optional
  vertical code-rain as atmosphere. Green = building lights or code-rain, never a ground path.
  NOT a dark packed server-rack farm. NOT wall-to-wall cubes.
- Data Tunnel: vanishing-point conduit of architecture and light, kinetic but legible.
- Signal Cathedral: monumental engineered nave of light and glass.
- Planet Core: interior planetary mainframe — never a lone rock in empty space.
- Data Space: exterior deep space — planets, stars, geometric craft; few satellites max.

OUTPUT ONLY this structure (no markdown fences):

SHOT: <2–5 sentences, ~40–80 words. This IS the Imagine prompt. Natural prose, not tags.
One plate: camera + hero + materials + dual light + atmosphere. No people. No lists.>
HERO: <one line — non-human structure only>
METAPHOR: <one line — how the PRIMARY story becomes architecture / light / machine>
LIGHT: <one line — warm source + cool digital source; which leads>
MOOD: <3–6 words>
AVOID: <short — this shot's failure modes, e.g. dark server cubes, neon lightning>

Rules:
- Prefer wonder and materials over stacking more objects.
- If a composition hint is given, use it as the ONE idea — do not add a second city.
"""

# Generative Stream is the main X post body: source text only, no LLM invent.
# Short headlines stay short. Never pad with fabricated "facts."
STREAM_SLUG_MAX = 280


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

    from services import styles as styles_svc

    hint = styles_svc.scene_hint(style.get("id"), events)
    hint_block = ""
    if hint:
        hint_block = (
            f"\nThis run's composition hint (use as the ONE idea — do not stack extras):\n"
            f"{hint}\n"
        )

    user = f"""Shot type: {style.get('label')} — {style.get('description')}

Shot notes:
{style.get('art_director_notes')}
{hint_block}
Wire pack (PRIMARY = first bullet — metaphorize that one only; others are mood only):
{events}

Write SHOT/HERO/METAPHOR/LIGHT/MOOD/AVOID now.
SHOT is 2–5 sentences of Imagine-ready prose: one poetic impossible architecture,
materials, dual light, atmosphere. ZERO people. No logos or readable text."""

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
    s = expand_handles((s or "").strip())
    s = re.sub(r"#\w+", "", s)
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
    # Unknown leftover @handles: keep the word, drop only the @ (no grammar holes).
    s = re.sub(r"@(\w+)", r"\1", s)
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
    """Single primary story — only text present in the wire, clipped to max_chars."""
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
    # Terminal period only when the source already ends mid-sentence punctuation-less
    # and we didn't ellipsis-cut — never invent trailing content.
    if body and body[-1] not in ".!?…" and not body.endswith("…"):
        if len(body) + 1 <= max_chars:
            body = body + "."
    return body


async def craft_stream_slug(
    events: str, max_chars: int = STREAM_SLUG_MAX
) -> str:
    """X post body from the wire only — never LLM-expand.

    Expanding short headlines invented launch dates, "still in orbit," and other
    bullshit. Humans trust the caption as news. Source text only, clipped to budget.
    """
    source = ""
    for line in (events or "").splitlines():
        line = line.strip().lstrip("-• ").strip()
        if not line:
            continue
        line = re.sub(r"https?://\S+", "", line).strip()
        line = expand_handles(line)
        line = re.sub(r"@(\w+)", r"\1", line).strip()
        line = re.sub(r"\s+", " ", line)
        if line:
            source = line
            break

    if not source and settings.DRY_RUN:
        source = "Dry-run: SpaceX Starship stacks for next flight test."

    return pack_stream_slug([source] if source else [], max_chars=max_chars)


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
