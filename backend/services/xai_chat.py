"""Grok steps: art director + caption + Generative Stream slug (Session 2)."""

from __future__ import annotations

import re

import httpx

from config import settings
from services.xai_client import client

ART_DIRECTOR_SYSTEM = """You are art director for "Planet Hack" (@tunastarlink).
3D digital CGI cyberspace. One clear hero PLUS rich supporting atmosphere.
Mid density: cinematic and layered — NOT empty black void, NOT scrapyard soup.

Output ONLY this structure (no markdown fences):

CAMERA: <one line — wide 16:9, strong perspective>
HERO: <one line — single main subject>
CHAOS: <one line — ONE metaphor for the PRIMARY (first) news story>
PALETTE: <expressive franchise colors: void black + cyan + magenta + gold and/or acid-green as style allows>
MOOD: <3–6 words>
DETAIL: <1–2 sentences: supporting rings/light/particles/structure — frame must feel inhabited>

Rules:
- Metaphor from the PRIMARY (first) story only. Extra headlines are background mood only.
- No politicians, flags, logos, readable headlines, or real maps.
- Match the shot type notes. Prefer power and depth over sparse minimalism.
- Planet Core especially: interior mainframe scale with layered rings/light — never a lone rock in empty space.
- No readable text in the image.
"""

CAPTION_SYSTEM = (
    "Caption for Planet Hack digital art. "
    "1–2 short atmospheric sentences about the place in the image. "
    "Max ~180 characters. No hashtags (we append them). No URLs. No newlines. "
    "Do not name politicians or paste the news headline. Mood only."
)

# Generative Stream is the real news payload (main caption is mood-only).
# Leave headroom for "Generative Stream: " + " #StyleCamel" inside 280.
STREAM_SLUG_MAX = 240

STREAM_SLUG_SYSTEM = (
    "Rewrite the PRIMARY news headline as a natural X sentence for a creative account. "
    "Lead with the news fact (who/what). Sound like a wire desk, not a promo or diary. "
    "Prefer a complete sentence. No hashtags. No URLs. No 'the poster said'."
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

Wire pack (PRIMARY = first bullet — metaphorize that one only; others are mood):
{events}

Do NOT paint text/headlines. Fill CAMERA/HERO/CHAOS/PALETTE/MOOD/DETAIL now."""

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


def _clean_headline_piece(s: str) -> str:
    """Normalize one headline for Generative Stream (no hashtags/URLs)."""
    import re

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
    """
    Pack 1–3 cleaned headlines into the Generative Stream body.

    Main caption is mood-only; this reply is the actual news payload — use the
    full budget. Primary first (complete if possible), then " · " secondaries.
    """
    cleaned: list[str] = []
    junk_re = re.compile(
        r"\b(day\s*\d+|leetcode|follow me|link in bio|becoming better|"
        r"jimothy|frog-like|tokenized|perp game|watch until the end|"
        r"launch your own|in 60 seconds)\b",
        re.I,
    )
    for h in headlines:
        piece = _clean_headline_piece(h)
        if len(piece) < 20 or junk_re.search(piece):
            continue
        cleaned.append(piece)

    if not cleaned:
        return "A live story from the wire."

    parts: list[str] = []
    for piece in cleaned:
        if not parts:
            # Primary gets the full budget if alone; leave room for siblings when present
            parts.append(piece)
            continue
        sep = " · "
        trial = sep.join(parts + [piece])
        if len(trial) <= max_chars:
            parts.append(piece)
            continue
        # Partial secondary if we still have meaningful room
        used = len(sep.join(parts)) + len(sep)
        room = max_chars - used
        if room >= 36:
            parts.append(_fit_text(piece, room))
        break

    body = " · ".join(parts)
    if len(body) > max_chars:
        body = _fit_text(body, max_chars)
    # Single headline: end with period if it doesn't already
    if " · " not in body and body and body[-1] not in ".!?…":
        if len(body) + 1 <= max_chars:
            body = body + "."
    return body


async def craft_stream_slug(
    events: str, max_chars: int = STREAM_SLUG_MAX
) -> str:
    """Generative Stream body — the real news text (main post is atmospheric only).

    Packs primary + secondary wire titles up to max_chars (~240 so the full
    reply fits in 280 with prefix + style hashtag).
    """
    import re

    candidates: list[str] = []
    for line in (events or "").splitlines():
        line = line.strip().lstrip("-• ").strip()
        if not line:
            continue
        line = re.sub(r"https?://\S+", "", line).strip()
        line = re.sub(r"@\w+", "", line).strip()
        line = re.sub(r"\s+", " ", line)
        # Prefer title before long em-dash body
        title = line.split(" — ")[0].strip()
        if title:
            candidates.append(title)

    if settings.DRY_RUN:
        return pack_stream_slug(
            candidates
            or ["A multi-headline wire pack, remixed as digital weather."],
            max_chars=max_chars,
        )

    packed = pack_stream_slug(candidates, max_chars=max_chars)
    if packed and packed != "A live story from the wire.":
        return packed

    # Fallback: LLM rewrite of primary only when raw titles were unusable
    user = (
        f"Wire pack (PRIMARY first):\n{events[:500]}\n\n"
        "One news sentence from the PRIMARY headline (who/what). "
        f"Max {max_chars} characters. No hashtags. No 'the poster said'."
    )
    if settings.EDGE_TEXT == "lemonade":
        text = await _lemonade_chat(STREAM_SLUG_SYSTEM, user, max_tokens=120)
    else:
        text = await _xai_chat(STREAM_SLUG_SYSTEM, user, max_tokens=120, temperature=0.3)
    return pack_stream_slug([text or ""] + candidates, max_chars=max_chars)


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
