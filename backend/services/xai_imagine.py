"""xAI Imagine image generation + dry-run cyberspace placeholder PNG."""

from __future__ import annotations

import io
import math
from typing import Any

import httpx
from PIL import Image, ImageDraw

from config import settings
from services.xai_client import client


def _placeholder_png(run_id: str, style_label: str) -> bytes:
    """Local digital-grid placeholder — still NOT real Imagine. Labels it clearly."""
    w, h = 1024, 1024
    img = Image.new("RGB", (w, h), (4, 6, 14))
    draw = ImageDraw.Draw(img)

    # Perspective grid (tunnel floor / wall)
    cx, cy = w // 2, h // 2
    for i in range(1, 24):
        t = i / 24
        inset = int(40 + t * 420)
        color = (0, int(40 + t * 160), int(60 + t * 140))
        draw.rectangle([inset, inset, w - inset, h - inset], outline=color, width=1)

    for angle_deg in range(0, 360, 15):
        rad = math.radians(angle_deg)
        x2 = cx + int(math.cos(rad) * 700)
        y2 = cy + int(math.sin(rad) * 700)
        draw.line([(cx, cy), (x2, y2)], fill=(0, 80, 110), width=1)

    # Neon "packet" blocks
    accents = [(0, 255, 220), (255, 40, 140), (80, 255, 80), (255, 200, 40)]
    blocks = [
        (120, 180, 280, 260),
        (700, 140, 880, 300),
        (160, 620, 340, 820),
        (640, 580, 900, 860),
        (420, 360, 600, 520),
    ]
    for i, box in enumerate(blocks):
        draw.rectangle(box, outline=accents[i % len(accents)], width=2)
        # pixel steps on edge
        x0, y0, x1, y1 = box
        for x in range(x0, x1, 8):
            draw.point((x, y0), fill=accents[i % len(accents)])
            draw.point((x, y1), fill=accents[i % len(accents)])

    # Core glow
    for r in range(90, 20, -8):
        shade = min(255, 40 + (90 - r) * 3)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(shade // 3, shade, shade))

    draw.text((36, 36), "PLANET HACK  ·  DRY_RUN PLACEHOLDER", fill=(0, 220, 200))
    draw.text((36, 56), f"{style_label}  ·  {run_id}", fill=(160, 180, 200))
    draw.text((36, 980), "not Imagine — local grid only", fill=(100, 120, 140))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def generate_image(prompt: str, run_id: str, style_label: str) -> tuple[bytes, dict[str, Any]]:
    """Return (png_bytes, stats). stats includes egress_bytes for Starlink panel."""
    if settings.DRY_RUN:
        data = _placeholder_png(run_id, style_label)
        return data, {
            "model": "dry-run-placeholder",
            "egress_bytes": 0,
            "source": "local",
        }

    c = client()
    resp = c.images.generate(
        model=settings.XAI_IMAGE_MODEL,
        prompt=prompt,
        n=1,
    )
    item = resp.data[0]
    url = getattr(item, "url", None)
    b64 = getattr(item, "b64_json", None)

    if b64:
        import base64

        raw = base64.b64decode(b64)
        return raw, {
            "model": settings.XAI_IMAGE_MODEL,
            "egress_bytes": len(raw),
            "source": "b64",
        }

    if not url:
        raise RuntimeError("Imagine response had neither url nor b64_json")

    with httpx.Client(timeout=120.0, follow_redirects=True) as http:
        r = http.get(url)
        r.raise_for_status()
        raw = r.content

    return raw, {
        "model": settings.XAI_IMAGE_MODEL,
        "egress_bytes": len(raw),
        "source": "url",
        "image_url": url[:200],
    }
