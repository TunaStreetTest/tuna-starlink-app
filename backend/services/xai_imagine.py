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


def imagine_generate_kwargs(prompt: str) -> dict[str, Any]:
    """OpenAI-SDK kwargs for xAI Imagine. Never send `size` — it 400s."""
    kwargs: dict[str, Any] = {
        "model": settings.XAI_IMAGE_MODEL,
        "prompt": prompt,
        "n": 1,
    }
    extra: dict[str, Any] = {}
    aspect = (settings.XAI_IMAGE_ASPECT_RATIO or "").strip()
    resolution = (settings.XAI_IMAGE_RESOLUTION or "").strip().lower()
    if aspect:
        extra["aspect_ratio"] = aspect
    if resolution in ("1k", "2k"):
        extra["resolution"] = resolution
    if extra:
        kwargs["extra_body"] = extra
    return kwargs


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
    # xAI Imagine: aspect_ratio + resolution only. OpenAI `size` (e.g. 1792x1024)
    # 400s the request; the old retry then dropped 16:9/1k and still billed.
    kwargs = imagine_generate_kwargs(prompt)

    try:
        resp = c.images.generate(**kwargs)
    except Exception as e:
        import logging

        logging.getLogger("tuna-starlink.imagine").warning(
            "Imagine first attempt failed (%s): %s", type(e).__name__, e
        )
        # Keep aspect + resolution. Only drop them if extra_body itself was rejected.
        retry = {
            "model": settings.XAI_IMAGE_MODEL,
            "prompt": prompt + "\n\nAspect: wide cinematic 16:9 landscape, full-frame horizontal composition.",
            "n": 1,
            "extra_body": dict((kwargs.get("extra_body") or {})),
        }
        if not retry["extra_body"]:
            retry.pop("extra_body")
        resp = c.images.generate(**retry)
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


def _response_to_bytes(resp: Any) -> tuple[bytes, str]:
    """Pull image bytes from an ImagesResponse item."""
    import base64

    item = resp.data[0]
    b64 = getattr(item, "b64_json", None)
    if b64:
        return base64.b64decode(b64), "b64"
    url = getattr(item, "url", None)
    if not url:
        raise RuntimeError("Imagine response had neither url nor b64_json")
    with httpx.Client(timeout=120.0, follow_redirects=True) as http:
        r = http.get(url)
        r.raise_for_status()
        return r.content, "url"


def develop_from_field(
    field_png: bytes,
    prompt: str,
    run_id: str,
    style_label: str,
    *,
    input_fidelity: str = "high",
) -> tuple[bytes, dict[str, Any]]:
    """Structure-locked finish: field PNG is composition DNA; edit may only polish.

    xAI /images/edits expects JSON: image.url = data:image/png;base64,...
    (OpenAI SDK multipart is rejected.) Layout stays owned by the stream field.
    """
    if settings.DRY_RUN:
        return field_png, {
            "model": "dry-run-field",
            "egress_bytes": 0,
            "source": "local-field",
            "develop": "passthrough",
        }

    import base64
    import logging

    log = logging.getLogger("tuna-starlink.imagine")
    b64 = base64.b64encode(field_png).decode("ascii")
    data_url = f"data:image/png;base64,{b64}"
    endpoint = f"{settings.XAI_BASE_URL.rstrip('/')}/images/edits"
    headers = {
        "Authorization": f"Bearer {settings.XAI_API_KEY}",
        "Content-Type": "application/json",
    }

    def _post(payload: dict[str, Any]) -> bytes:
        with httpx.Client(timeout=180.0, follow_redirects=True) as http:
            r = http.post(endpoint, headers=headers, json=payload)
            if r.status_code >= 400:
                raise RuntimeError(f"edit HTTP {r.status_code}: {r.text[:400]}")
            body = r.json()
        data = (body.get("data") or [None])[0]
        if not data:
            raise RuntimeError(f"edit empty data: {body!r}"[:400])
        if data.get("b64_json"):
            return base64.b64decode(data["b64_json"])
        url = data.get("url")
        if not url:
            raise RuntimeError(f"edit missing url/b64: {data!r}"[:400])
        with httpx.Client(timeout=120.0, follow_redirects=True) as http:
            img = http.get(url)
            img.raise_for_status()
            return img.content

    base_payload: dict[str, Any] = {
        "model": settings.XAI_IMAGE_MODEL,
        "prompt": prompt,
        "n": 1,
        "image": {"url": data_url},
    }
    resolution = (settings.XAI_IMAGE_RESOLUTION or "").strip().lower()
    if resolution in ("1k", "2k"):
        base_payload["resolution"] = resolution
    # Try high-fidelity first (may be ignored if unsupported)
    attempts = [
        {**base_payload, "input_fidelity": input_fidelity},
        base_payload,
    ]
    last_err: Exception | None = None
    for i, payload in enumerate(attempts):
        try:
            raw = _post(payload)
            return raw, {
                "model": settings.XAI_IMAGE_MODEL,
                "egress_bytes": len(raw),
                "source": "edit-json",
                "develop": "edit",
                "input_fidelity": payload.get("input_fidelity"),
                "attempt": i + 1,
            }
        except Exception as e:
            last_err = e
            log.warning("develop attempt %s failed: %s", i + 1, e)

    raise RuntimeError(
        f"structure-locked develop failed (edit required for path 3): {last_err}"
    ) from last_err
