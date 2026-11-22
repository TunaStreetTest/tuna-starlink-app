"""Load Planet Hack style presets from prompts/styles.yaml."""

from __future__ import annotations

import random
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from config import settings

_STYLES_FILE = Path(__file__).resolve().parent.parent / "prompts" / "styles.yaml"

# Fallback if yaml missing fields
_LANE_DEFAULT = "space"
_HASHTAG_DEFAULT = "PlanetHack"

# Data Space compositions. The hero noun comes from the vehicle lock, not these lines.
# Never a centered HUD globe / circuit-board Earth, never a generic stand-in ship.
_DATA_SPACE_SCENES = (
    "SCENE: 3/4 fly-by, the hero vehicle LARGE in the foreground, cyan light on real panels, "
    "night-side Earth with city lights behind, thick cyan-magenta data rings, volumetric "
    "magenta-green plume, starfield. No Tron outlines, no HUD, no circuit globe.",
    "SCENE: the hero vehicle climbing past night-side Earth; city lights on continents; "
    "cyan packet rings; the vehicle fills a third of the frame. Real materials. "
    "No press photo, no targeting reticle, no glow-stick shuttle.",
    "SCENE: high oblique on Earth with one massive cyan-magenta telemetry ring as a belt; "
    "the hero vehicle cutting across the ring; real oceans and city lights, "
    "not PCB continents, not Tron.",
    "SCENE: vehicle-forward in the lower-right, Earth and rings receding; "
    "cyan seam-light, magenta ring light, volumetric green exhaust, starfield depth.",
    "SCENE: close 3/4 on the vehicle body with Earth limb and a neon ring behind it; "
    "light wrapping metal; no floating crystals, no clipart globe, no outlines.",
    "SCENE: rings-forward — luminous cyan-magenta packet streams ellipse around Earth, "
    "the hero vehicle riding the ring; the planet still looks like a planet.",
)

_VEHICLE_LEAD = {
    "starship": (
        "The hero is SpaceX Starship itself: the real stainless-steel ship with its body flaps, "
        "recognizable as Starship. Neon light on that steel. Not a generic spacecraft, not Falcon 9, "
        "not a glow-stick shuttle, not a press photo."
    ),
    "falcon": (
        "The hero is a real SpaceX Falcon 9 first stage, the flight hardware, not a redesign. "
        "A long white cylinder. A black interstage band at the TOP, and exactly four square "
        "titanium grid fins mounted on that interstage, never on the middle of the body. "
        "Four landing legs at the BASE only, folded against the engine skirt or just opened. "
        "Exactly nine Merlin engines in an octaweb: one engine in the center and eight around it. "
        "No tenth engine. No rounded nose cone on the booster. No payload fairing on the first stage. "
        "No heat-shield tiles. No body flaps. No wings. The white paint stays white. "
        "Cyan and magenta are rim light and plume light, not stripes painted down the fuselage. "
        "Not Starship, not a concept rocket, not a glow-stick shuttle, not a press photo."
    ),
    "starlink": (
        "The hero is a short train of real Starlink satellites. Each one is a flat rectangular "
        "bus with one long solar wing, the same shape repeated in a line. Recognizable as "
        "Starlink. Not a user dish on a pole, not a cubesat, not a generic satellite with "
        "random antennas. Not Falcon 9, not Starship. If a scene line says vehicle, it means "
        "this satellite train. Neon is rim light on the panels and the wings. "
        "No engines, no plume, no nose cone. Not a press photo, not a glow-stick."
    ),
}

_STARSHIP_RE = re.compile(r"\b(starship|super\s*heavy|raptor)\b", re.I)
_FALCON_RE = re.compile(r"\bfalcon(?:\s*9|\s*heavy)?\b", re.I)
_STARLINK_RE = re.compile(r"\bstarlink\b|direct[- ]to[- ]cell", re.I)
_SPACE_RE = re.compile(
    r"\b(spacex|starbase|orbital|satellite|constellation|booster|"
    r"cape canaveral|vandenberg|slc-\d+)\b",
    re.I,
)
_TECH_RE = re.compile(
    r"\b(nvidia|geforce|gpu|gpus|blackwell|hopper|cuda|h100|h200|b100|b200|gb200|"
    r"tsmc|semiconductor|tensor\s*core|datacenter|data center|chipmaker)\b",
    re.I,
)
_AI_RE = re.compile(
    r"\b(openai|anthropic|claude|chatgpt|gpt-?\d|gemini|grok|xai|x\.ai|"
    r"llm|llms|large language|foundation model|open[- ]weights|"
    r"optimus|dojo|robotaxi|full self[- ]driving|fsd|mistral|llama|deepmind)\b",
    re.I,
)

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


def version_ids(style_id: str) -> list[str]:
    """Core skin plus older skins stored under that style. The core id stays the name."""
    data = _raw()
    styles = data.get("styles") or {}
    val = styles.get(style_id) or {}
    extra = [k for k in (val.get("versions") or {}) if k and k != "core"]
    return ["core", *extra]


def pick_version(style_id: str, rng: random.Random | None = None) -> str:
    ids = version_ids(style_id)
    if rng is None:
        return random.choice(ids)
    return rng.choice(ids)


def primary_line(events: str) -> str:
    """First bullet. Later lines are mood and do not pick the object or the core."""
    for line in (events or "").splitlines():
        text = line.strip().lstrip("-").strip()
        if text:
            return text
    return (events or "").strip()


def next_version(style_id: str, last: str | None) -> str:
    """The skin after `last`. Order is core, then each older skin, then core again."""
    ids = version_ids(style_id)
    if not ids:
        return "core"
    if not last or last not in ids:
        return ids[0]
    return ids[(ids.index(last) + 1) % len(ids)]


def recent_looks(limit: int = 24) -> list[dict[str, str]]:
    """Newest complete plates, as style id and version."""
    from services import art_store

    out: list[dict[str, str]] = []
    for meta in art_store.list_runs(160):
        if meta.get("status") != "complete":
            continue
        sid = str(meta.get("style_id") or "")
        if not sid:
            continue
        out.append({"id": sid, "version": str(meta.get("style_version") or "core")})
        if len(out) >= limit:
            break
    return out


def choose_story_core(texts: list[str], recent_cores: list[str]) -> str:
    """Core for the next plate.

    The newest story wins, unless that core was just used and another fresh
    story maps somewhere else. A wire that is all one subject stays on it.
    """
    if not texts:
        return "signal-cathedral"
    cores = [core_for_story(text) for text in texts]
    last = recent_cores[0] if recent_cores else None
    recent_n: dict[str, int] = {}
    for core in recent_cores[:4]:
        recent_n[core] = recent_n.get(core, 0) + 1
    best_i = 0
    best_key: tuple[int, int, int] | None = None
    for i, core in enumerate(cores):
        key = (1 if core == last else 0, recent_n.get(core, 0), i)
        if best_key is None or key < best_key:
            best_key = key
            best_i = i
    return cores[best_i]


def get_style(style_id: str | None = None, version: str | None = None) -> dict[str, Any]:
    data = _raw()
    styles = data.get("styles") or {}
    key = style_id or settings.DEFAULT_STYLE or data.get("default") or next(iter(styles), "")
    if key not in styles:
        raise ValueError(f"unknown style {key!r}; known: {list(styles)}")
    val = styles[key]
    versions = val.get("versions") or {}
    chosen = (version or "core").strip() or "core"
    over = {}
    if chosen != "core":
        if chosen not in versions:
            raise ValueError(f"unknown version {chosen!r} of {key!r}; known: {version_ids(key)}")
        over = versions[chosen] or {}
    series = series_info()
    label = val.get("label", key)
    hashtag = val.get("hashtag") or _camel(label)
    return {
        "id": key,
        "label": label,
        "description": val.get("description", ""),
        "hashtag": hashtag,
        "lane": (val.get("lane") or _LANE_DEFAULT).strip().lower(),
        "version": chosen,
        "version_scene": (over.get("scene") or "").strip(),
        "art_director_notes": (over.get("art_director_notes") or val.get("art_director_notes") or "").strip(),
        "prompt_seed": (over.get("prompt_seed") or val.get("prompt_seed") or "").strip(),
        "series_name": series["name"],
        "series_tagline": series["tagline"],
        "shared_lock": series["shared_lock"],
    }


def vehicle_lead(kind: str | None) -> str:
    return _VEHICLE_LEAD.get(kind or "") or ""


def vehicle_kind(text: str) -> str | None:
    """Starship, Falcon, or Starlink satellites. Starship wins, then Falcon."""
    if _STARSHIP_RE.search(text or ""):
        return "starship"
    if _FALCON_RE.search(text or ""):
        return "falcon"
    if _STARLINK_RE.search(text or ""):
        return "starlink"
    return None


def core_for_story(text: str) -> str:
    """Which of the five cores draws this story.

    Starship, Falcon 9, and Starlink satellites are Data Space, and the plate
    shows that object. Other space news is Planet Core. Nvidia and chip news
    are Rootkit City. AI news is Data Tunnel. Anything else is Signal Cathedral.
    """
    blob = text or ""
    if vehicle_kind(blob):
        return "data-space"
    if _SPACE_RE.search(blob):
        return "planet-core"
    if _TECH_RE.search(blob):
        return "rootkit-city"
    if _AI_RE.search(blob):
        return "data-tunnel"
    return "signal-cathedral"


def search_lane_for_core(core: str) -> str | None:
    """X/RSS lane to consult for a core. None means take the story as it is."""
    return {
        "data-space": "space",
        "planet-core": "space",
        "data-tunnel": "ai",
        "rootkit-city": "gpu",
    }.get(core)


def style_for_story(
    events: str,
    rng: random.Random | None = None,
    recent: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Pick a core from the primary story, then the next skin of that core.

    A passed rng keeps the old random skin, for tests. The cron passes recent
    looks, or none, and walks core then each older skin.
    """
    text = primary_line(events)
    core = core_for_story(text)
    if rng is not None:
        version = pick_version(core, rng)
    else:
        looks = recent_looks() if recent is None else recent
        last = next((row["version"] for row in looks if row.get("id") == core), None)
        version = next_version(core, last)
    style = get_style(core, version=version)
    kind = vehicle_kind(text) if core == "data-space" else None
    if kind:
        style["vehicle"] = kind
    return style


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


def scene_hint(
    style_id: str | None,
    salt: str,
    version: str | None = None,
    version_scene: str = "",
    vehicle: str | None = None,
) -> str:
    """Composition hint for the art director — not appended to the Imagine prompt."""
    sid = str(style_id or "")
    key = salt or sid
    hint = ""
    if version and version != "core" and version_scene:
        hint = version_scene.strip()
    elif sid in ("data-space", "data_space"):
        hint = _scene_pick(key, _DATA_SPACE_SCENES, "data-space")
    elif sid in ("rootkit-city", "rootkit_city"):
        hint = _scene_pick(key, _ROOTKIT_CITY_SCENES, "rootkit-city")
    if sid in ("data-space", "data_space"):
        kind = vehicle or vehicle_kind(primary_line(salt))
        lead = _VEHICLE_LEAD.get(kind or "")
        if lead:
            hint = f"{lead} {hint}".strip()
    return hint


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


def build_imagine_prompt(
    art_brief: str,
    style: dict[str, Any],
    source_text: str = "",
) -> str:
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

    shot_or_seed = shot or seed
    lead = shot_or_seed
    kind = None
    scene = (style.get("version_scene") or "").strip()
    version = str(style.get("version") or "core")
    older_scene = scene if scene and version not in ("", "core") else ""
    if style_id in ("data-space", "data_space"):
        kind = style.get("vehicle") or vehicle_kind(primary_line(source_text))
        vehicle = _VEHICLE_LEAD.get(kind or "")
        lead = "\n\n".join(part for part in (vehicle, older_scene, shot_or_seed) if part)
    elif older_scene:
        lead = "\n\n".join(part for part in (older_scene, shot_or_seed) if part)
    if kind == "falcon":
        lock = (
            "Wide 16:9 cinematic CGI of a real Falcon 9 first stage. White cylinder. "
            "Black interstage at the top. Exactly four grid fins, only on that interstage. "
            "Four landing legs, only at the base. Exactly nine Merlin engines in an octaweb: "
            "one center, eight around. No tenth engine. No nose cone. No heat-shield tiles. "
            "No body flaps. No wings. The white paint stays white. Neon is rim light and the "
            "plume, not stripes on the fuselage. Not Starship. Not a concept rocket. "
            "Zero humans, no logos, no readable text."
        )
    elif kind == "starlink":
        lock = (
            "Wide 16:9 cinematic CGI of real Starlink satellites: flat rectangular buses, "
            "each with one long solar wing, flying as a short train. Not a user dish, "
            "not a cubesat, not Falcon 9, not Starship. Neon is rim light on the panels. "
            "Earth or a starfield behind. Zero humans, no logos, no readable text."
        )
    elif style_id in ("data-space", "data_space"):
        lock = (
            "Wide 16:9 cinematic CGI. Real metal and planet surface; neon is LIGHT on "
            "those materials and the rings. The named vehicle has presence and is that "
            "vehicle, not a stand-in. Zero humans, no logos, "
            "no readable text. No Tron outlines, no glow-stick shuttle, no HUD reticle, "
            "no circuit-board globe, no floating crystals, no clipart Earth, no god-rays, "
            "no press photo with the neon stripped off."
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
