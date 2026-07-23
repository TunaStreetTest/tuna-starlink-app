"""Kaleidoscope stream raster — cathedral-style radial symmetry across all styles.

Single story text → mirrored sectors (structure lock) → images.edit polish.
Module name kept as ring_address for import stability; mode is kaleidoscope.
"""

from __future__ import annotations

import hashlib
import io
import math
import re
from typing import Any

from PIL import Image, ImageDraw, ImageFilter

VOID = (6, 8, 16)
CYAN = (0, 255, 220)
MAGENTA = (255, 40, 140)
GOLD = (255, 200, 40)
ACID = (80, 255, 80)
WHITE = (230, 240, 255)


def stream_from_events(events: str) -> str:
    """Single source — full story text into the raster."""
    body = ""
    for line in (events or "").splitlines():
        line = line.strip().lstrip("-• ").strip()
        if not line:
            continue
        line = re.sub(r"https?://\S+", "", line).strip()
        line = re.sub(r"@\w+", "", line).strip()
        line = re.sub(r"\s+", " ", line)
        body = line
        break
    if not body:
        body = re.sub(r"\s+", " ", (events or "").strip())
    if len(body) > 480:
        body = body[:479].rsplit(" ", 1)[0] + "…"
    return body or "empty stream"


def char_class(ch: str) -> str:
    if ch.isdigit():
        return "digit"
    if ch.isalpha():
        return "vowel" if ch.lower() in "aeiou" else "consonant"
    if ch.isspace():
        return "space"
    return "punct"


def _style_id(style: dict[str, Any] | None) -> str:
    return ((style or {}).get("id") or "signal-cathedral").lower()


def class_color(cls: str, style_id: str, intensity: float = 1.0) -> tuple[int, int, int]:
    """Palette emphasis per style; still franchise cyan/magenta base."""
    if style_id == "rootkit-city":
        base = {
            "digit": ACID,
            "vowel": CYAN,
            "consonant": MAGENTA,
            "space": (20, 40, 30),
            "punct": GOLD,
        }[cls]
    elif style_id == "data-tunnel":
        base = {
            "digit": CYAN,
            "vowel": (0, 200, 255),
            "consonant": MAGENTA,
            "space": (10, 20, 40),
            "punct": ACID,
        }[cls]
    elif style_id == "planet-core":
        base = {
            "digit": GOLD,
            "vowel": CYAN,
            "consonant": MAGENTA,
            "space": (30, 20, 10),
            "punct": (255, 160, 40),
        }[cls]
    else:  # signal-cathedral default kaleidoscope
        base = {
            "digit": GOLD,
            "vowel": CYAN,
            "consonant": MAGENTA,
            "space": (25, 20, 45),
            "punct": ACID,
        }[cls]
    return tuple(max(0, min(255, int(c * intensity))) for c in base)


def analyze(stream: str) -> dict[str, Any]:
    counts = {k: 0 for k in ("digit", "vowel", "consonant", "space", "punct")}
    digits: list[str] = []
    for ch in stream:
        c = char_class(ch)
        counts[c] += 1
        if c == "digit":
            digits.append(ch)
    h = hashlib.sha256(stream.encode()).digest()
    # 6–12 mirrored sectors from stream hash
    n_sectors = 6 + (h[0] % 7)
    return {
        "len": len(stream),
        "counts": counts,
        "digits": "".join(digits),
        "digit_sum": sum(int(d) for d in digits) if digits else 0,
        "hash8": h.hex()[:8],
        "n_sectors": n_sectors,
        "stream": stream,
    }


def _lead_color(style_id: str) -> tuple[int, int, int]:
    if style_id == "rootkit-city":
        return ACID
    if style_id == "data-tunnel":
        return CYAN
    if style_id == "planet-core":
        return GOLD
    return GOLD  # cathedral leading


def render_field(
    stream: str,
    style: dict[str, Any] | None = None,
    w: int = 1400,
    h: int = 800,
) -> Image.Image:
    """Kaleidoscope: stream paints one wedge, mirrored full-frame to the corners."""
    sid = _style_id(style)
    analysis = analyze(stream)
    n = int(analysis["n_sectors"])
    sector = math.tau / n

    img = Image.new("RGB", (w, h), VOID)
    draw = ImageDraw.Draw(img)
    cx, cy = w / 2, h / 2
    # reach corners so it's not a lonely circle on black
    max_r = math.hypot(cx, cy) * 1.02

    # Build color samples from stream (repeat to fill facets)
    samples: list[tuple[int, int, int]] = []
    for i, ch in enumerate(stream):
        cls = char_class(ch)
        intensity = 0.55 + 0.45 * ((ord(ch) % 16) / 15.0)
        samples.append(class_color(cls, sid, intensity))
    if not samples:
        samples = [CYAN, MAGENTA, GOLD]

    # Facet rings × sectors = stained-glass / kaleidoscope cells
    n_rings = 8 if sid != "data-tunnel" else 10
    lead = _lead_color(sid)

    for ring in range(n_rings):
        r0 = max_r * (ring / n_rings) * 0.98
        r1 = max_r * ((ring + 1) / n_rings) * 0.98
        for s in range(n * 2):  # half-sectors for mirror look
            a0 = (s / (n * 2)) * math.tau
            a1 = ((s + 1) / (n * 2)) * math.tau
            # color from stream position
            idx = (ring * 7 + s * 3 + (ord(stream[s % len(stream)]) if stream else 0)) % len(
                samples
            )
            col = samples[idx]
            # polygon pie cell
            steps = 6
            pts = [(cx + math.cos(a0) * r0, cy + math.sin(a0) * r0)]
            for k in range(steps + 1):
                a = a0 + (a1 - a0) * (k / steps)
                pts.append((cx + math.cos(a) * r1, cy + math.sin(a) * r1))
            pts.append((cx + math.cos(a1) * r0, cy + math.sin(a1) * r0))
            draw.polygon(pts, fill=col, outline=lead)

    # Radial mirror spines (kaleidoscope seams)
    for s in range(n):
        a = s * sector
        x2 = cx + math.cos(a) * max_r
        y2 = cy + math.sin(a) * max_r
        width = 3 if sid == "signal-cathedral" else 2
        draw.line([(cx, cy), (x2, y2)], fill=lead, width=width)

    # Stream-driven spark nodes along spines (still addressable DNA)
    for i, ch in enumerate(stream):
        spine = i % n
        a = spine * sector + (ord(ch) % 7) * 0.02
        t = 0.12 + 0.85 * ((i + 1) / max(len(stream), 1))
        r = max_r * t
        x = cx + math.cos(a) * r
        y = cy + math.sin(a) * r
        cls = char_class(ch)
        size = 5 if cls != "digit" else 6 + int(ch) // 2
        draw.ellipse(
            [x - size, y - size, x + size, y + size],
            fill=class_color(cls, sid, 1.0),
            outline=WHITE,
        )

    # Center jewel
    draw.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=(10, 12, 24), outline=lead, width=3)
    draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=MAGENTA if sid != "rootkit-city" else ACID)
    draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=WHITE)

    # Style-specific overlay accent
    if sid == "data-tunnel":
        # horizontal motion bars through center
        for dy in (-40, 0, 40):
            draw.line([(0, cy + dy), (w, cy + dy)], fill=(0, 180, 200), width=1)
    elif sid == "rootkit-city":
        # acid infiltration diameter
        draw.line([(0, cy), (w, cy)], fill=ACID, width=3)
    elif sid == "planet-core":
        for rr in (80, 140, 200):
            draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=GOLD, width=1)

    glow = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    img = Image.blend(img, glow, 0.18)
    return img


def field_png_bytes(stream: str, style: dict[str, Any] | None = None) -> bytes:
    img = render_field(stream, style=style)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _style_phosphor(style: dict[str, Any] | None) -> str:
    sid = _style_id(style)
    label = (style or {}).get("label") or sid
    notes = {
        "signal-cathedral": (
            f"{label}: stained-glass kaleidoscope nave — faceted neon panes, gold leading, "
            "volumetric light through mirrored geometry."
        ),
        "data-tunnel": (
            f"{label}: kaleidoscope through a speed tunnel — radial symmetry + vanishing motion, "
            "cyan conduit glass, magenta accents."
        ),
        "planet-core": (
            f"{label}: kaleidoscope planetary core — mirrored mainframe facets, gold fracture seams, "
            "deep cyan-magenta pressure light."
        ),
        "rootkit-city": (
            f"{label}: kaleidoscope circuit city — angular mirrored facets, acid-green rewrite seam, "
            "magenta nodes on dark cyan grid glass."
        ),
    }
    return notes.get(sid, f"{label}: full-frame digital kaleidoscope CGI.")


def build_raster_brief(analysis: dict[str, Any], style: dict[str, Any] | None = None) -> str:
    c = analysis["counts"]
    return (
        f"RASTER: kaleidoscope\n"
        f"SECTORS: {analysis.get('n_sectors')}\n"
        f"PACKET_LEN: {analysis['len']}\n"
        f"HASH: {analysis['hash8']}\n"
        f"NODES: consonants={c['consonant']} vowels={c['vowel']} "
        f"digits={c['digit']} punct={c['punct']}\n"
        f"STORY: {(analysis.get('stream') or '')[:200]}\n"
        f"{_style_phosphor(style)}"
    )


def build_develop_prompt(
    analysis: dict[str, Any], style: dict[str, Any] | None = None
) -> str:
    story = (analysis.get("stream") or "")[:220]
    n = analysis.get("n_sectors") or 8
    return (
        "DEVELOP this exact image. Do not redesign the composition. "
        f"Keep the same kaleidoscope symmetry ({n} mirrored sectors), facet colors, "
        "center jewel, and radial seams. "
        "FULL FRAME edge-to-edge — pattern must reach the corners, no large empty black margins. "
        "Premium 3D CGI: stained-glass / crystal / chrome facets, volumetric light, "
        "cinematic 16:9 full-bleed, dense luminous kaleidoscope atmosphere. "
        "No readable text, letters, numbers, logos, or people. "
        f"Story DNA (mood only, never paint as text): {story}. "
        f"Fingerprint {analysis.get('hash8', '')}. "
        f"{_style_phosphor(style)}"
    )


def compile_packet(
    events: str, style: dict[str, Any] | None = None
) -> dict[str, Any]:
    stream = stream_from_events(events)
    analysis = analyze(stream)
    return {
        "raster_mode": "kaleidoscope",
        "develop_mode": "edit_high_fidelity",
        "stream_packet": stream,
        "analysis": analysis,
        "field_png": field_png_bytes(stream, style=style),
        "art_brief": build_raster_brief(analysis, style),
        "art_prompt": build_develop_prompt(analysis, style),
    }
