"""Load Planet Hack style presets from prompts/styles.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from config import settings

_STYLES_FILE = Path(__file__).resolve().parent.parent / "prompts" / "styles.yaml"

# Fallback if yaml missing fields
_LANE_DEFAULT = "space"
_HASHTAG_DEFAULT = "PlanetHack"

# Per-run scene recipes for data-space (keeps spatial variety without boring tunnels)
_DATA_SPACE_SCENES = (
    "SCENE: single large holographic data-planet as hero, cracked wireframe continents, "
    "thin orbital data rings, deep indigo void, soft gold limb light, no ship.",
    "SCENE: multi-planet system — three to five worlds at different depths and sizes, "
    "one closer hero planet with data-ring, others receding, no ship required.",
    "SCENE: bright star (or binary) dominates the frame with lens-flare energy; "
    "one small data-planet as secondary; star is the emotional hero.",
    "SCENE: SpaceX-inspired geometric starship as pure machine silhouette "
    "(stainless stacked body, abstract grid fins, engine plume light) — no logos, "
    "no crew windows with people, alone against deep space and sparse data-mesh.",
    "SCENE: SpaceX-inspired geometric starship near a large data-planet, "
    "orbital approach composition, plume and planet limb light, no people.",
    "SCENE: Starlink-like constellation mesh of many small satellites as a glowing net "
    "wrapping a dark planet; planet + mesh are the dual hero; no crewed ship.",
    "SCENE: planetary system edge-on with a bright accretion-like data disk and "
    "one ringed world; cinematic scale; optional tiny geometric ship as accent only.",
    "SCENE: two planets in conjunction (near-overlap) with a star rising between them; "
    "holographic telemetry arcs; no people.",
)


@lru_cache(maxsize=1)
def _raw() -> dict[str, Any]:
    with _STYLES_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def reload_styles() -> None:
    _raw.cache_clear()


def series_info() -> dict[str, str]:
    data = _raw()
    s = data.get("series") or {}
    return {
        "name": (s.get("name") or "Planet Hack").strip(),
        "tagline": (s.get("tagline") or "").strip(),
        "shared_lock": (s.get("shared_lock") or "").strip(),
    }


def list_styles() -> list[dict[str, str]]:
    data = _raw()
    styles = data.get("styles") or {}
    out = []
    for key, val in styles.items():
        out.append(
            {
                "id": key,
                "label": val.get("label", key),
                "description": val.get("description", ""),
                "hashtag": val.get("hashtag") or _camel(val.get("label") or key),
                "lane": val.get("lane") or _LANE_DEFAULT,
            }
        )
    return out


def _camel(label: str) -> str:
    import re

    parts = re.split(r"[\s_\-]+", (label or "").strip())
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def get_style(style_id: str | None = None) -> dict[str, Any]:
    data = _raw()
    styles = data.get("styles") or {}
    key = style_id or settings.DEFAULT_STYLE or data.get("default") or next(iter(styles), "")
    if key not in styles:
        raise ValueError(f"unknown style {key!r}; known: {list(styles)}")
    val = styles[key]
    series = series_info()
    label = val.get("label", key)
    hashtag = val.get("hashtag") or _camel(label)
    return {
        "id": key,
        "label": label,
        "description": val.get("description", ""),
        "hashtag": hashtag,
        "lane": (val.get("lane") or _LANE_DEFAULT).strip().lower(),
        "art_director_notes": (val.get("art_director_notes") or "").strip(),
        "prompt_seed": (val.get("prompt_seed") or "").strip(),
        "series_name": series["name"],
        "series_tagline": series["tagline"],
        "shared_lock": series["shared_lock"],
    }


def _palette_steer(art_brief: str, style_id: str) -> str:
    """Nudge Imagine off the default cyan/magenta soak with a stable per-run accent."""
    import hashlib

    accents = (
        "Palette steer: ice-white and cobalt primary; neon only as thin edge accents.",
        "Palette steer: amber-copper heat with graphite metal; violet only in deep shadows.",
        "Palette steer: deep indigo and soft gold; phosphor green as sparse signal only.",
        "Palette steer: steel-silver and white-hot core light; electric violet rims.",
        "Palette steer: charcoal and bronze architecture; acid-green as a single path accent.",
        "Palette steer: amethyst and cool white beams; cyan only in distant fog.",
    )
    h = hashlib.sha256(f"{style_id}|{art_brief[:120]}".encode()).digest()
    return accents[h[0] % len(accents)]


def _data_space_scene(art_brief: str) -> str:
    """Pick a spatial recipe so runs vary: planet(s), star, SpaceX-inspired ship, etc."""
    import hashlib

    h = hashlib.sha256(art_brief.encode()).digest()
    return _DATA_SPACE_SCENES[h[0] % len(_DATA_SPACE_SCENES)]


def build_imagine_prompt(art_brief: str, style: dict[str, Any]) -> str:
    seed = (style.get("prompt_seed") or "").strip()
    brief = art_brief.strip()
    lock = (style.get("shared_lock") or "").strip()
    style_id = str(style.get("id") or "")
    steer = _palette_steer(brief, style_id)
    quality = (
        "Render quality: ultra-premium cinematic still, sharp micro-detail, clean geometry, "
        "deep volumetric light, no people or human silhouettes."
    )
    parts = [seed]
    if style_id in ("data-space", "data_space"):
        parts.append(_data_space_scene(brief or seed))
    parts.extend([brief, steer, quality, lock])
    return "\n\n".join(p for p in parts if p)
