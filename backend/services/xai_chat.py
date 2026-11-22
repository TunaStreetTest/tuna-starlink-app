"""Grok steps: art director brief + Tuna Starlink X post.

Art director may metaphorize the still. News facts in the X body must appear in the wire.
"""

from __future__ import annotations

import html
import re

import httpx

from config import settings
from services.wire_quality import expand_handles
from services.xai_client import client

# Neon-night matrix CGI. Heaven filter is the failure mode (god-rays, photoreal
# Earth postcards, silver VFX). One hero, full cyan/magenta/acid-green spectrum.
ART_DIRECTOR_SYSTEM = """You are the lead art director for "Planet Hack" (@tunastarlink).
Write a Grok Imagine brief: premium CGI, neon as LIGHT on real materials.

CRAFT:
- ONE idea. One camera. One hero.
- Materials: metal grain, heat-tile, glass, silicon etch. Light wraps the form.
  Atmospheric depth, haze as air — not church shafts.
- Neon is illumination ON those materials (cyan/magenta/green on seams, rings,
  packet glow, engine light). NOT Tron tube outlines. NOT glow-stick silhouettes
  on flat black. NOT an After Effects preset.
- Color: void black depths + electric cyan + hot magenta + acid-green.

SERIES LOCK:
- Wide 16:9. Zero humans / silhouettes / faces.
- No logos, flags, readable UI, lightning-bolt weather, lava, scrapyard soup.
- BAN cheap render: Tron line-art, neon-outline spaceships, vector HUD, clipart Earth,
  targeting reticles, After Effects tunnel templates.
- BAN heaven: church god-rays, washed gold, empty nave, National Geographic press
  photo with no neon.
- Metaphor the PRIMARY wire story only (SpaceX / GPU / AI / silicon / orbital).

STYLE (one hero, not a packed catalog):
- Data Space: cinematic CGI FROM orbit (July 28). 3/4 fly-by. The object pool is
  Starship, Falcon 9, and Starlink satellites, and the lock names which one.
  Starship is the stainless-steel ship with body flaps. Falcon 9 is the real first
  stage: white cylinder, black interstage, four grid fins only at the top, four
  landing legs only at the base, nine Merlin engines in an octaweb. No nose cone,
  no heat tiles, no body flaps, no racing stripes on the white paint. Starlink is
  a train of flat satellites, each with one solar wing. Never a generic ship and
  never the other object. Cyan signal light on that real hull; night-side Earth
  with city lights; cyan-magenta data rings; volumetric plume. NEVER Tron outlines.
  NEVER a centered HUD globe. NEVER a circuit-board Earth.
- Planet Core: interior mainframe — jacked wireframe Earth in a neon lattice of
  real metal-glass. NEVER a washed globe in god-rays.
- Data Tunnel: physical conduit (metal-glass ribs) packed with cyan/magenta packet
  torrents. Far glow is NEON, not a white sun. NOT a vector tunnel template.
- Signal Cathedral: neon signal-glass nave, not church light shafts through fog.
- Rootkit City: luminous digital city INSIDE the computer on a PCB grid. One neon-lit
  megastructure of glass and silicon. Green = building lights or code-rain.
  NOT a packed server farm. NOT Tron wireframe cubes.

OUTPUT ONLY this structure (no markdown fences):

SHOT: <2–5 sentences, ~40–80 words. This IS the Imagine prompt. Natural prose, not tags.
One plate: camera + hero + materials + neon-as-light + atmosphere. No people. No lists.>
HERO: <one line — non-human structure only>
METAPHOR: <one line — how the PRIMARY story becomes architecture / light / machine>
LIGHT: <one line — which neon leads (cyan / magenta / green) on which materials>
MOOD: <3–6 words>
AVOID: <short — always include Tron outlines / cheap vector render; Data Space also HUD globe>

Rules:
- Premium CGI with neon light, not outline stickers.
- If a composition hint is given, use it as the ONE idea — do not add a second city.
"""

# Ledger line: source text only, no LLM invent. The X body is craft_tuna_post.
STREAM_SLUG_MAX = 900
POST_MIN_CHARS = 160
POST_TARGET_MAX = 480
POST_HARD_MAX = 4000

TUNA_POST_SYSTEM = """You write the X post for @tunastarlink (Tuna Starlink).
Bio: I do stuff with AI and Data. Powered by Starlink.

Three beats. Then stop. The link is added for you. Do not write a URL.

1) ARTICLE. First paragraph. Normal words. This is the part a person shares.
   Use the wire's own words: the name, the verb, the number, and the quote.
   Do not shorten "freezes at awkward Tesla Argentina launch: 'I don't know
   what to say'" into "froze at the launch". Do not robot it. Do not add a
   second news paragraph. A one-line restatement that drops the quote or the
   figure is wrong. The publisher keeps the wire headline when the rewrite
   drops those words.

2) PLATE. Blank line, then broken robot speak. The plate is coming in through
   the Starlink dish. Short lines. Dropped words. Name the style. The delivery
   is not finished in this paragraph.

3) DELIVERED. Blank line, then ONE robot line that finishes the delivery.
   End on that line.

Shape to copy (facts here are only an example):

Falcon 9 B1103-5 just put Starlink Group 17-49 up from Vandenberg.

Plate inbound. Dish open. Data Space coming through the Starlink link. Cyan on the hull. Magenta in the plume. Pixels still in the pipe. Dish holding. Render not seated. Link still open. Frame still empty. Not done.

Delivered. Plate on the glass.

Rules:
- Every news fact MUST appear in the WIRE. No invented dates, orbits, outcomes,
  counts, or extra news. The robot lines may only talk about the plate, the dish,
  and this studio's Starlink link.
- Do not claim the subject of the wire uses Starlink unless the wire says so.
- The delivery line starts just after 280 characters, so Show more reveals
  that line and then the link. Do not write anything after it.
- Do NOT recap the art-director SHOT. No hashtags. No URLs. No @handles.
- No grok slop ("this architecture is a metaphor for…").
- Output ONLY the post body.
"""


async def craft_art_brief(events: str, style: dict) -> str:
    if settings.DRY_RUN:
        return (
            f"SHOT: Wide 16:9 neon-night matrix CGI of {style.get('label')}: one impossible "
            f"digital structure in saturated cyan, magenta, and acid-green on void black, "
            f"no people, no god-rays.\n"
            f"HERO: single digital architectural form matching style\n"
            f"METAPHOR: neon machine metaphor for the wire story\n"
            f"LIGHT: cyan leads, magenta nodes, acid-green sparks\n"
            f"MOOD: neon root access\n"
            f"AVOID: god-rays, photoreal Earth postcard, silver CGI, humans, logos"
        )

    from services import styles as styles_svc

    hint = styles_svc.scene_hint(
        style.get("id"),
        events,
        version=style.get("version"),
        version_scene=style.get("version_scene") or "",
        vehicle=style.get("vehicle"),
    )
    hint_block = ""
    if hint:
        hint_block = (
            f"\nThis run's composition hint (use as the ONE idea — do not stack extras):\n"
            f"{hint}\n"
        )
    vehicle_block = ""
    if style.get("vehicle") and style.get("id") in ("data-space", "data_space"):
        lead = styles_svc.vehicle_lead(style.get("vehicle"))
        if lead:
            vehicle_block = f"\nVEHICLE LOCK (obey this noun): {lead}\n"

    user = f"""Shot type: {style.get('label')} — {style.get('description')}

Shot notes:
{style.get('art_director_notes')}
{hint_block}{vehicle_block}
Wire pack (PRIMARY = first bullet — metaphorize that one only; others are mood only):
{events}

Write SHOT/HERO/METAPHOR/LIGHT/MOOD/AVOID now.
SHOT is 2–5 sentences of Imagine-ready prose: one neon impossible architecture,
void black, cyan/magenta/acid-green as the scene color. ZERO people. No logos,
no god-rays, no press photo with the neon stripped off. If a vehicle lock is set,
the hero is that exact ship."""

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
    """Normalize one headline for the source-only ledger line."""
    s = html.unescape(s or "")
    s = s.replace("\xa0", " ")
    s = expand_handles(s.strip())
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


def _primary_wire(events: str) -> str:
    source = ""
    for line in (events or "").splitlines():
        line = line.strip().lstrip("-• ").strip()
        if not line:
            continue
        line = html.unescape(line).replace("\xa0", " ")
        line = re.sub(r"https?://\S+", "", line).strip()
        line = expand_handles(line)
        line = re.sub(r"@(\w+)", r"\1", line).strip()
        line = re.sub(r"\s+", " ", line)
        if line:
            source = line
            break
    return source


async def craft_stream_slug(
    events: str, max_chars: int = STREAM_SLUG_MAX
) -> str:
    """Ledger / never-reuse line from the wire only — never LLM-expand.

    Expanding short headlines invented launch dates, "still in orbit," and other
    bullshit. Facts stay source-only. The public X body is craft_tuna_post.
    """
    source = _primary_wire(events)
    if not source and settings.DRY_RUN:
        source = "Dry-run: SpaceX Starship stacks for next flight test."
    return pack_stream_slug([source] if source else [], max_chars=max_chars)


def _clean_post_body(text: str, limit: int = POST_HARD_MAX) -> str:
    body = (text or "").strip()
    body = re.sub(r"^```(?:\w+)?\s*|\s*```$", "", body).strip()
    body = re.sub(r"#\w+", "", body)
    body = re.sub(r"https?://\S+", "", body)
    body = re.sub(r"@(\w+)", r"\1", body)
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = re.sub(r"[^\S\n]+", " ", body).strip()
    if len(body) <= limit:
        return body
    cut = body[: max(limit - 1, 1)].rsplit(" ", 1)[0].rstrip(",;:·-–—")
    if not cut:
        cut = body[: max(limit - 1, 1)]
    return cut + "…"


_DRY_TUNA_POST = (
    "SpaceX Starship stacks for the next flight test.\n\n"
    "Plate inbound. Dish open. Data Space on the Starlink link. Steel hull. Not done.\n\n"
    "Delivered. Plate on the glass."
)


async def craft_tuna_post(
    events: str,
    style: dict | None = None,
    art_brief: str = "",
) -> str:
    """X body: the wire headline, then the plate arriving in robot speak."""
    wire = _primary_wire(events)
    if not wire and settings.DRY_RUN:
        wire = "Dry-run: SpaceX Starship stacks for next flight test."

    if settings.DRY_RUN:
        return _DRY_TUNA_POST

    shot = ""
    if art_brief:
        from services.styles import _extract_shot_paragraph

        shot = _extract_shot_paragraph(art_brief)[:280]

    style_label = (style or {}).get("label") or "Planet Hack"
    user = f"""WIRE (facts you may use — nothing else is a fact):
{wire}

STYLE: {style_label}
PLATE (mood only — do not recap as a shot list): {shot or style_label}

Write the X post now."""

    model = (settings.XAI_CHAT_MODEL or "").strip()
    if settings.EDGE_TEXT == "lemonade":
        raw = await _lemonade_chat(TUNA_POST_SYSTEM, user, max_tokens=400)
    else:
        raw = await _xai_chat(
            TUNA_POST_SYSTEM,
            user,
            max_tokens=400,
            temperature=0.55,
            model=model,
        )
    body = _clean_post_body(raw, POST_HARD_MAX)
    return finish_robot_post(body, wire, style_label)


_OUTLET_TAIL = re.compile(
    r"\s+[-–|]\s+(?:[A-Z][\w.&'+-]*|\w+\.[A-Za-z]{2,})"
    r"(?:\s+(?:[A-Z][\w.&'+-]*|\w+\.[A-Za-z]{2,})){0,3}\s*$"
)
def article_from_wire(wire: str) -> str:
    """The share line, in the wire's words. Drop the outlet and a repeated title."""
    text = html.unescape(wire or "").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if " — " in text:
        left, right = text.split(" — ", 1)
        left_key = re.sub(r"\W+", "", left.lower())[:40]
        right_key = re.sub(r"\W+", "", right.lower())[:40]
        if left_key and right_key.startswith(left_key[:24]):
            text = left.strip()
    text = _OUTLET_TAIL.sub("", text).strip(" -–—|")
    text = re.sub(r"\s+", " ", text).strip()
    if text and text[-1] not in ".!?…":
        text += "."
    return text


def _plate_paragraph(text: str, style_label: str) -> str:
    label = (style_label or "Planet Hack").strip() or "Planet Hack"
    fallback = f"Plate inbound. Dish open. {label} on the Starlink link. Not done."
    for part in (text or "").split("\n\n"):
        part = " ".join(part.split())
        if not part or part.startswith("Delivered."):
            continue
        if "Plate inbound" in part or "Not done." in part:
            return part
    return fallback


def finish_robot_post(body: str, wire: str, style_label: str = "") -> str:
    """Headline in the wire's words, then the plate inbound, then one delivery line.

    The model rewrite is not the share line. "Freezes" and a quoted phrase were
    getting softened into a shorter sentence. The wire headline is the top bit.
    """
    head = article_from_wire(wire)
    if not head:
        head = pack_stream_slug([wire], max_chars=220) or "A live story from the wire."
    middle = _plate_paragraph(body, style_label)
    ending = "Delivered. Plate on the glass."
    text = f"{head}\n\n{middle}\n\n{ending}"
    if len(text) <= POST_TARGET_MAX:
        return text
    room = POST_TARGET_MAX - len(head) - len(ending) - 4
    if room < 40:
        if len(head) + 2 + len(ending) <= POST_TARGET_MAX:
            return f"{head}\n\n{ending}"
        return _clean_post_body(f"{head}\n\n{ending}", POST_TARGET_MAX)
    kept = _fit_text(middle, room).removesuffix("…").rstrip()
    return f"{head}\n\n{kept}\n\n{ending}"


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
