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

# Per-run scene recipes for data-space (spatial variety; keep satellite counts low)
_DATA_SPACE_SCENES = (
    "SCENE: single large holographic data-planet as hero, cracked wireframe continents, "
    "thin orbital data rings, deep indigo void, soft gold limb light, no ship, "
    "no satellite swarm.",
    "SCENE: multi-planet system — three to five worlds at different depths and sizes, "
    "one closer hero planet with data-ring, others receding, no ship, no satellite swarm.",
    "SCENE: bright star (or binary) dominates the frame with lens-flare energy; "
    "one small data-planet as secondary; star is the emotional hero; no satellite swarm.",
    "SCENE: SpaceX-inspired geometric starship as pure machine silhouette "
    "(stainless stacked body, abstract grid fins, engine plume light) — no logos, "
    "no crew windows with people, alone against deep space; at most 1–3 distant craft glints.",
    "SCENE: SpaceX-inspired geometric starship near a large data-planet, "
    "orbital approach composition, plume and planet limb light, no people, "
    "no dense satellite mesh.",
    "SCENE: dark planet with sparse orbital infrastructure — only a few (3–8) small "
    "satellite points of light on a thin ring, NOT hundreds; planet is the hero.",
    "SCENE: planetary system edge-on with a bright accretion-like data disk and "
    "one ringed world; cinematic scale; optional single tiny geometric ship as accent only.",
    "SCENE: two planets in conjunction (near-overlap) with a star rising between them; "
    "holographic telemetry arcs; no people; no satellite swarm.",
)

# Per-run cityscape recipes for rootkit-city (layout variety; keep neon spectrum)
_ROOTKIT_CITY_SCENES = (
    "SCENE: sprawling coastal circuit metropolis — towers step down to a luminous "
    "cyan-magenta data-sea horizon; acid-green rewrite snakes inland; neon night.",
    "SCENE: floating voxel districts stacked at different altitudes over a dark die-grid "
    "base; bridges of cyan/magenta light between blocks; phosphor rain.",
    "SCENE: deep canyon street between colossal GPU-die skyscrapers; low camera looking "
    "along the neon canyon toward a bright acid-green root-access core.",
    "SCENE: elevated megastructure ring-city above a lower sprawl; one vertical "
    "acid-green infiltration beam from the ring into a cyan-magenta grid below.",
    "SCENE: hexagonal die-district from a high oblique angle — unique block layout, "
    "different tower heights; rewrite path as a bright green circuit trace on cyan streets.",
    "SCENE: night skyline with a planetary data-horizon behind the towers; "
    "silhouette variety (spires, cubes, lattice stacks); full cyan/magenta/green neon glow.",
    "SCENE: industrial silicon waterfront — machine-form cooling geometry, packet piers, "
    "vapor neon cyan and magenta; acid-green rewrite along the docks.",
    "SCENE: fractured mid-infiltration city — half still dark cyan grid, half rewritten "
    "in acid-green and hot magenta; clear front-line of the rootkit spread.",
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
    """Vary which neon leads — keep full cyan/magenta/acid-green spectrum, never desaturate."""
    import hashlib

    # Spectrum shifts inside the franchise neon night — not monochrome / graphite replacements.
    accents = (
        "COLOR SPECTRUM: cyan-led neon night — electric cyan grids dominate, hot magenta "
        "nodes secondary, acid-green path as hero accent; void black depths; gold metal rims optional.",
        "COLOR SPECTRUM: magenta-led neon night — hot magenta signal clusters lead, cyan streets "
        "underneath, acid-green rewrite cut; void black; copper edge warmth optional.",
        "COLOR SPECTRUM: acid-green-led neon night — phosphor green rewrite floods the frame, "
        "cyan structure supports, magenta pulses at nodes; void black; white-hot core sparks.",
        "COLOR SPECTRUM: gold-warm neon night — soft gold / amber window and limb light warms "
        "metal, still full cyan grids + magenta nodes + acid-green path (do not drop neon).",
        "COLOR SPECTRUM: ice-spectrum neon — ice-cyan and white-hot cores lead, violet-magenta "
        "depth glows, acid-green filaments; still a saturated neon night, not grey metal.",
        "COLOR SPECTRUM: balanced triad neon — equal electric cyan + hot magenta + acid green "
        "across architecture and data; high saturation; void black negative space.",
    )
    h = hashlib.sha256(f"{style_id}|{art_brief[:120]}".encode()).digest()
    return accents[h[0] % len(accents)]


def _scene_pick(art_brief: str, scenes: tuple[str, ...], style_id: str = "") -> str:
    """Stable per-run scene recipe from art_brief (+ style) so layouts vary."""
    import hashlib

    h = hashlib.sha256(f"{style_id}|{art_brief}".encode()).digest()
    return scenes[h[0] % len(scenes)]


def _data_space_scene(art_brief: str) -> str:
    """Pick a spatial recipe so runs vary: planet(s), star, SpaceX-inspired ship, etc."""
    return _scene_pick(art_brief, _DATA_SPACE_SCENES, "data-space")


def _rootkit_city_scene(art_brief: str) -> str:
    """Pick a cityscape recipe so rootkit-city is not the same skyline every run."""
    return _scene_pick(art_brief, _ROOTKIT_CITY_SCENES, "rootkit-city")


def build_imagine_prompt(art_brief: str, style: dict[str, Any]) -> str:
    seed = (style.get("prompt_seed") or "").strip()
    brief = art_brief.strip()
    lock = (style.get("shared_lock") or "").strip()
    style_id = str(style.get("id") or "")
    steer = _palette_steer(brief, style_id)
    quality = (
        "Render quality: ultra-premium cinematic still, sharp micro-detail, clean geometry, "
        "deep volumetric light, saturated neon color spectrum, no people or human silhouettes."
    )
    parts = [seed]
    if style_id in ("data-space", "data_space"):
        parts.append(_data_space_scene(brief or seed))
    elif style_id in ("rootkit-city", "rootkit_city"):
        parts.append(_rootkit_city_scene(brief or seed))
    parts.extend([brief, steer, quality, lock])
    return "\n\n".join(p for p in parts if p)
