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
CHAOS: <one line — ONE metaphor for the PRIMARY (first) news story>
PALETTE: <limited; name 2–3 colors + void>
MOOD: <3–6 words>
DETAIL: <1–2 sentences max; keep air in the frame>

Rules:
- Metaphor from the PRIMARY (first) story only. Extra headlines are background mood only.
- No politicians, flags, logos, readable headlines, or real maps.
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
    "Rewrite the PRIMARY news headline as a short, natural X sentence for a creative account. "
    "Lead with the news fact (who/what). Sound like a wire desk, not a promo or diary. "
    "Max 140 characters. No hashtags. No URLs. No 'the poster said'."
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


async def craft_stream_slug(events: str) -> str:
    """Short human sentence for Generative Stream reply (no hashtags).

    Wire packs list 2–3 headlines; PRIMARY is first. Prefer that cleaned title —
    RSS-style headlines already read well on X without LLM rewrite.
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

    first = candidates[0] if candidates else ""

    junk_re = re.compile(
        r"\b(day\s*\d+|leetcode|follow me|link in bio|becoming better|"
        r"jimothy|frog-like|tokenized|perp game|watch until the end|"
        r"launch your own|in 60 seconds)\b",
        re.I,
    )

    def _finish(s: str) -> str:
        s = re.sub(r"#\w+", "", (s or "").strip())
        s = re.sub(
            r"^(the poster|someone|this user|the author)\s+(reported|said|shared|posted)\s+",
            "",
            s,
            flags=re.I,
        ).strip()
        # strip leading emoji / wire prefixes for a cleaner Generative Stream
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
        s = re.sub(r"\s+", " ", s)
        if not s:
            return "A live story from the wire."
        if s[0].islower():
            s = s[0].upper() + s[1:]
        if len(s) > 130:
            s = s[:129].rsplit(" ", 1)[0].rstrip(",;:-") + "…"
        elif s[-1] not in ".!?…":
            s = s + "."
        return s

    if settings.DRY_RUN:
        return _finish(first or "A multi-headline wire pack, remixed as digital weather.")

    # Prefer cleaned PRIMARY title when solid; else next non-junk candidate.
    for cand in candidates:
        if len(cand) >= 24 and not junk_re.search(cand):
            return _finish(cand)

    user = (
        f"Wire pack (PRIMARY first):\n{events[:500]}\n\n"
        "One short news sentence from the PRIMARY headline only (who/what). "
        "No hashtags. No 'the poster said'."
    )
    if settings.EDGE_TEXT == "lemonade":
        text = await _lemonade_chat(STREAM_SLUG_SYSTEM, user, max_tokens=60)
    else:
        text = await _xai_chat(STREAM_SLUG_SYSTEM, user, max_tokens=60, temperature=0.3)
    return _finish(text or first or "A live story from the wire.")


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
