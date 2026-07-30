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

# Per-run cityscape recipes for rootkit-city — dense digital city INSIDE the computer.
# Lots of buildings: GPU-die towers, CPU cores, data racks. Green on ARCHITECTURE or
# vertical matrix code-rain between towers — never a ground path / bolt / beam.
_ROOTKIT_CITY_SCENES = (
    "SCENE: dense GPU-die metropolis packing the frame — silicon skyscrapers and CPU-core "
    "cubes rise from a cyan PCB street grid; magenta facade nodes; acid-green window bands "
    "on select towers; optional vertical matrix code-rain in the canyons between buildings.",
    "SCENE: low street-level canyon deep inside the mainframe — colossal circuit-board "
    "towers and rack-lit data spires crowd both sides; vanishing-point cyan grid road; "
    "one mid-ground tower fully acid-green as the rootkit hero; dense layered architecture.",
    "SCENE: elevated view over a sprawling die-grid city — mixed heights of GPU blocks, "
    "memory-bank mid-rises, lattice CPU stacks; every tower etched with circuitry; "
    "cyan streets; magenta roof clusters; green as PCB right-angle etch on skins only.",
    "SCENE: CPU core district — cubic processor towers with pin-grid bases and cache-ring "
    "balconies; dense surrounding data towers; reflective black silicon plaza; "
    "one green-glass core building anchors the story; no ground energy paths.",
    "SCENE: dense rack-city high oblique — server-tower rows and transistor districts "
    "packed wall-to-wall; cyan grid arteries; magenta signal panels; rootkit = one "
    "green-glowing district block (solid building lights); vertical code-rain optional.",
    "SCENE: wafer-stack skyline — layered translucent silicon plates as megablocks, "
    "dense tower forests on each tier; cyan edge light; sparse green window bands; "
    "frame filled with buildings, never empty sky or lone object.",
    "SCENE: floating mesh districts of data towers linked by thin straight light bridges "
    "over a lower sprawl of circuit mid-rises; packed skyline; Tron/Hackers density; "
    "acid-green only on select facade panels and bridge rail lights.",
    "SCENE: root-access CPU plaza — dark cyan grid floor, ring of dense surrounding "
    "GPU/data towers filling every edge of the frame; hero is a single cubic green-glass "
    "CPU core building at center (solid architecture, not a glowing crack or beam).",
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
    """Compose Imagine prompt: SHOT paragraph leads; seed/lock are light guardrails.

    Best Grok Imagine stills win on ONE poetic architecture + materials + dual light,
    not a stack of competing rule blocks. Keep franchise locks short.
    """
    seed = (style.get("prompt_seed") or "").strip()
    brief = (art_brief or "").strip()
    style_id = str(style.get("id") or "")
    if style_id in ("rootkit-city", "rootkit_city"):
        brief = _sanitize_rootkit_brief(brief)

    shot = _extract_shot_paragraph(brief)
    if style_id in ("rootkit-city", "rootkit_city"):
        shot = _sanitize_rootkit_brief(shot)

    # Lead with the cinematic SHOT — this is what quality Imagine work looks like.
    parts: list[str] = []
    if shot:
        parts.append(shot)
    elif seed:
        parts.append(seed)

    # Light style geometry cue (not a second full prompt).
    if style_id in ("data-space", "data_space"):
        parts.append(_data_space_scene(brief or seed))
    elif style_id in ("rootkit-city", "rootkit_city"):
        parts.append(_rootkit_city_scene(brief or seed))
        parts.append(
            "Dense digital city inside the computer: packed silicon/GPU/CPU data towers "
            "filling the frame; cyan PCB grid streets; acid-green as building lights or "
            "vertical matrix code-rain between towers only — no glowing ground paths, "
            "lightning bolts, or jagged energy weather."
        )
    elif seed and shot and seed not in shot:
        # Short style anchor when SHOT is present (seed is fallback lead otherwise).
        first_line = seed.split("\n", 1)[0].strip()
        if first_line:
            parts.append(first_line)

    # Dual-light material bar (from showcase DNA), not a neon dump checklist.
    parts.append(
        "Finished ultra-premium VFX still, wide 16:9, photoreal materials (glass, metal, "
        "silicon micro-detail), dual light (warm practical + cool digital), deep atmospheric "
        "depth of field, epic scale, legible architecture. No people or human silhouettes. "
        "No lava, no lightning-bolt weather, no scrapyard noise soup."
    )
    # Franchise hard rules — keep short so SHOT stays the hero.
    parts.append(
        "HARD: pure machine/architecture CGI only — zero humans; no logos, flags, or "
        "readable text; neon accents allowed but subordinate to the one hero structure."
    )
    return "\n\n".join(p for p in parts if p)
