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

# Per-run scene recipes for data-space — cinematic craft + planet + neon rings (July 28).
# Never a centered HUD globe / circuit-board Earth.
_DATA_SPACE_SCENES = (
    "SCENE: 3/4 fly-by, metal machine-craft LARGE in the foreground with cyan seam-light, "
    "Earth behind with night-side city lights, thick cyan-magenta data rings, volumetric "
    "magenta/green plume, starfield. No Tron outlines, no HUD, no circuit globe.",
    "SCENE: Falcon/Starship-inspired metal booster climbing past night-side Earth; city lights "
    "on continents; cyan packet rings; craft fills a third of the frame. Real materials. "
    "No press photo, no targeting reticle, no glow-stick shuttle.",
    "SCENE: high oblique on Earth with one massive cyan-magenta telemetry ring as a belt; "
    "a single metal craft cutting across the ring; real oceans and city lights, "
    "not PCB continents, not Tron.",
    "SCENE: craft-forward — metal vehicle in the lower-right, Earth and rings receding; "
    "cyan seam-light, magenta ring light, volumetric green exhaust, starfield depth.",
    "SCENE: close 3/4 on the craft body (heat-tile / stainless) with Earth limb and a neon "
    "ring behind it; light wrapping metal; no floating crystals, no clipart globe, no outlines.",
    "SCENE: rings-forward — luminous cyan-magenta packet streams ellipse around Earth, "
    "one metal craft riding the ring; planet still looks like a planet.",
)

_DATA_SPACE_LAUNCH_SCENES = _DATA_SPACE_SCENES[:4]

# Per-run cityscape hints for rootkit-city — ONE neon hero on a PCB grid, not fog/space habitat.
# Fed to the art director only (not dumped into the Imagine prompt).
# Green on ARCHITECTURE or vertical code-rain — never a ground path / bolt / beam.
_ROOTKIT_CITY_SCENES = (
    "One luminous circuit-board canyon: a single neon-etched megatower as hero, "
    "glass-silicon facades, cyan streets, magenta nodes, optional vertical code-rain. "
    "Void black sky, saturated neon, no fogged silver, no god-rays.",
    "Elevated view of one impossible GPU-die citadel on a dark wafer-PCB plain — "
    "amber window dots inside, ice-cyan streets outside, magenta panels. No orbital void.",
    "Street-level look up a soaring silicon tower, circuit traces as stained neon "
    "architecture, a small empty plaza at its base, packed cyan/magenta grid around it.",
    "Reflective black silicon plaza with one cubic green-glass CPU keep; surrounding "
    "neon towers on a PCB grid — the keep is the story, not a wall of racks, not a ring in space.",
    "A wafer-plate acropolis: translucent stacked dies as terraces, one hero spire, "
    "cyan etch in the depths, magenta nodes, acid-green building lights, void black sky.",
    "Circuit-grid city at night: stacked neon towers on a cyan PCB street grid, "
    "magenta window clusters, optional code-rain, no people, no packed server racks, no heaven haze.",
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
    # Never describe green (or any color) as a path/bolt/beam — that becomes neon lightning.
    if style_id in ("rootkit-city", "rootkit_city"):
        accents = (
            "COLOR SPECTRUM: cyan-led city night — electric cyan grid streets dominate; "
            "hot magenta square panels on facades; acid-green only as steady facade window "
            "bands on select towers; void black. No green lines on the ground.",
            "COLOR SPECTRUM: magenta-led city night — magenta facade clusters lead; cyan streets; "
            "acid-green as one solid green-lit tower block; void black; soft amber windows optional.",
            "COLOR SPECTRUM: green-architecture night — one hero tower or district with solid "
            "acid-green glass/panels; rest of city cyan + magenta; void black. Green is BUILDING "
            "LIGHT, never a crack, path, bolt, beam, or river.",
            "COLOR SPECTRUM: warm-window city night — amber window dots on metal; cyan street grid; "
            "magenta nodes; sparse green facade accents. No molten orange sky.",
            "COLOR SPECTRUM: ice city night — ice-cyan streets and white-hot window cores; "
            "violet-magenta depth; acid-green as PCB right-angle etch glow on skins only.",
            "COLOR SPECTRUM: balanced triad on architecture — cyan streets, magenta panels, "
            "green windows distributed on towers; high saturation; controlled city glow only.",
        )
    else:
        accents = (
            "COLOR SPECTRUM: cyan-led neon night — electric cyan grids dominate, hot magenta "
            "nodes secondary, acid-green accents on structure; void black depths; cool metal rims optional.",
            "COLOR SPECTRUM: magenta-led neon night — hot magenta signal clusters lead, cyan "
            "structure underneath, acid-green accents; void black; soft copper warmth optional.",
            "COLOR SPECTRUM: acid-green-led neon night — phosphor green structural accents lead, "
            "cyan supports, magenta nodes; void black; white-hot core sparks on machines.",
            "COLOR SPECTRUM: warm-window neon night — soft amber window/limb light on metal, "
            "still full cyan + magenta + acid-green luminous color (do not drop neon).",
            "COLOR SPECTRUM: ice-spectrum neon — ice-cyan and white-hot cores lead, violet-magenta "
            "depth glows, acid-green filaments; saturated neon night, not grey metal.",
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


def scene_hint(style_id: str | None, salt: str) -> str:
    """Composition hint for the art director — not appended to the Imagine prompt."""
    sid = str(style_id or "")
    key = salt or sid
    if sid in ("data-space", "data_space"):
        pool = _DATA_SPACE_SCENES
        blob = (salt or "").lower()
        if any(w in blob for w in ("falcon", "starship", "starlink", "launch", "booster")):
            pool = _DATA_SPACE_LAUNCH_SCENES
        return _scene_pick(key, pool, "data-space")
    if sid in ("rootkit-city", "rootkit_city"):
        return _scene_pick(key, _ROOTKIT_CITY_SCENES, "rootkit-city")
    return ""


def _sanitize_rootkit_brief(brief: str) -> str:
    """Rewrite path/bolt metaphors so Imagine does not paint neon lightning."""
    import re

    if not brief:
        return brief
    # Common art-director phrases that become jagged green energy.
    replacements = (
        (r"\b(thin\s+)?acid[- ]green\s+(rootkit\s+)?(rewrite\s+)?(trace|path|seam|cut|route|line)s?\b",
         "acid-green facade lights on one tower"),
        (r"\b(rootkit\s+)?(rewrite|infiltration)\s+(trace|path|seam|beam|route|river|channel)s?\b",
         "green-lit rootkit tower block"),
        (r"\b(snaking|weaving|slicing|carving|fracturing|forking)\s+down\b", "concentrated in"),
        (r"\b(snaking|weaving|slicing|carving|fracturing|forking)\b", "concentrated"),
        (r"\bcarves a precise path\b", "anchors the district"),
        (r"\b(precise\s+)?path between towers\b", "tower block"),
        (r"\b(lightning|bolt|bolts|storm|storms)\b", "glow"),
        (r"\b(vertical\s+)?beams?\b", "tower lights"),
        (r"\b(jagged|crack|cracks|crackling)\b", "angular"),
        # Keep "matrix code-rain" / vertical glyph streams; only kill ground-path weather.
        (r"\b(molten|lava)\b", "neon haze"),
        (r"\bphosphor\s+rain\b", "matrix code-rain"),
        (r"\bdigital\s+river\b", "green-lit district"),
        (r"\bgreen\s+river\b", "green-lit block"),
        (r"\bcentral boulevard\b", "central district"),
    )
    out = brief
    for pat, rep in replacements:
        out = re.sub(pat, rep, out, flags=re.I)
    return out


def _extract_shot_paragraph(art_brief: str) -> str:
    """Pull SHOT: from art director brief; fall back to full brief."""
    import re

    text = (art_brief or "").strip()
    if not text:
        return ""
    m = re.search(
        r"(?is)^SHOT:\s*(.+?)(?=^\s*(?:HERO|METAPHOR|LIGHT|MOOD|AVOID|CAMERA|CHAOS|PALETTE|DETAIL)\s*:|\Z)",
        text,
        re.M,
    )
    if m:
        shot = re.sub(r"\s+", " ", m.group(1)).strip()
        if len(shot) > 40:
            return shot
    return text


def build_imagine_prompt(art_brief: str, style: dict[str, Any]) -> str:
    """Compose Imagine prompt: SHOT paragraph is the prompt.

    Best Grok Imagine stills win on ONE poetic architecture + materials + dual light.
    Do not stack scene recipes, density locks, and hard-rule essays after the SHOT —
    that is how Rootkit became a dark packed server farm.
    """
    seed = (style.get("prompt_seed") or "").strip()
    brief = (art_brief or "").strip()
    style_id = str(style.get("id") or "")
    if style_id in ("rootkit-city", "rootkit_city"):
        brief = _sanitize_rootkit_brief(brief)

    shot = _extract_shot_paragraph(brief)
    if style_id in ("rootkit-city", "rootkit_city"):
        shot = _sanitize_rootkit_brief(shot)

    lead = shot or seed
    if style_id in ("data-space", "data_space"):
        lock = (
            "Wide 16:9 cinematic CGI. Real metal and planet surface; neon is LIGHT on "
            "those materials and the rings. Craft has presence. Zero humans, no logos, "
            "no readable text. No Tron outlines, no glow-stick shuttle, no HUD reticle, "
            "no circuit-board globe, no floating crystals, no clipart Earth, no god-rays, "
            "no press-photo Starship with no neon."
        )
    else:
        lock = (
            "Wide 16:9 neon-night CGI on void black. Real materials; cyan, magenta, and "
            "acid-green as illumination on metal-glass, not outline stickers. Zero humans, "
            "no logos, no readable text. No Tron line-art, no After Effects tunnel preset, "
            "no god-rays, no church haze, no National Geographic postcard, no lightning, "
            "no lava, no packed server-rack farm."
        )
    return "\n\n".join(p for p in (lead, lock) if p)
