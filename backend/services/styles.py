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
# Tesla hardware that should appear as itself. Checked before the AI lane,
# which also names Optimus, robotaxi, and FSD.
_CYBERTRUCK_RE = re.compile(r"\bcyber[\s-]*trucks?\b", re.I)
_CYBERCAB_RE = re.compile(r"\bcyber[\s-]*cabs?\b|\brobotaxis?\b", re.I)
_ROBOT_RE = re.compile(
    r"\b(optimus|tesla\s*bots?|tesla\s*robots?|humanoid\s*robots?)\b",
    re.I,
)
_CABIN_RE = re.compile(
    r"\b(in[- ]?car|inside the (?:car|cabin|truck|cab)|cabin view|from the cabin|"
    r"driver'?s view|windshield|cabin)\b",
    re.I,
)
_FSD_RE = re.compile(r"\bfsd\b|full self[- ]?driving", re.I)
_TESLA_CONTEXT_RE = re.compile(
    r"\b(tesla|cyber(?:truck|cab)?s?|fsd|robotaxis?|optimus)\b",
    re.I,
)
# "data centers in space" / "SpaceX data centers", not a terrestrial server order.
_SPACE_DC_RE = re.compile(
    r"(?:"
    r"\b(?:data\s*cent(?:re|er)s?|datacent(?:re|er)s?|orbital\s+compute)\b"
    r".{0,80}\b(?:space|orbit|orbital|starlink|satellite|spacex)\b"
    r"|"
    r"\b(?:space|orbit|orbital|starlink|satellite|spacex)\b"
    r".{0,80}\b(?:data\s*cent(?:re|er)s?|datacent(?:re|er)s?|orbital\s+compute)\b"
    r")",
    re.I | re.S,
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

# Clear plates only. The dark neon skins stay for their own stories.
# Order is the walk: the 8kdxk7g hall, realistic space, the light tunnel, light architecture.
_SHAPE_PLATES = (
    "signal-cathedral",
    "data-space",
    "data-tunnel",
    "rootkit-city",
)

_SHAPE_LEAD = {
    "cybertruck": (
        "The hero is a real Tesla Cybertruck, large in the frame. Stainless polygonal "
        "exoskeleton, sharp wedge body, flat triangular glass, no grille, no round panels. "
        "It sits in the place described next. Not a pickup, not a sedan, not a concept car, "
        "not a rocket."
    ),
    "cybercab": (
        "The hero is a real Tesla Cybercab, large in the frame. A low two-seat robotaxi "
        "pod, smooth body, butterfly doors, no steering wheel, silver or warm metal. Empty. "
        "It sits in the place described next. Not a Model 3, not a van, not a Cybertruck, "
        "not a rocket."
    ),
    "cabin": (
        "The hero is an in-car view from the empty front seats of a Tesla. No driver, no "
        "passenger, no face, no hands on the wheel. A wide windshield looks out into the "
        "place described next. Minimal dash, one screen, a yoke or no wheel. You are inside "
        "the car. Not an exterior product shot."
    ),
    "robot": (
        "The hero is Tesla Optimus robots doing work in the place described next. Angular "
        "white-and-black humanoids, visible joints, real hands. One carries a crate, one "
        "walks, one works a station. No humans beside them. Not a statue, not a toy, not a "
        "generic android, not a rocket."
    ),
}

# Held out of version_ids. A test plate can ask for it. The hourly walk cannot,
# until Steven says this skin joins the rotation.
# seed by @Brewdreamery — 2026-11-26 — thin-film chrome, not the silk or the nebula.
_IRIDESCENT_NOTES = (
    "Surface only. Polished metal and thick glass. Cyan, magenta, violet, and amber "
    "are thin-film reflections sliding across that surface. The hero stays the hero "
    "and stays recognizable. Not neon tubes, not a silk sheet, not a painted nebula, "
    "not an abstract gem or a folded blob on a black field."
)
_IRIDESCENT_LOCK = (
    "MATERIAL: the subject named first stays large and recognizable. Polished metal "
    "and thick glass. Cyan, magenta, violet, and amber only as thin-film reflections "
    "on that surface. Not neon tubes, not a silk sheet, not a painted nebula, not an "
    "abstract blob."
)

_SHAPE_LOCK = (
    "Wide 16:9 finished VFX still. Photoreal materials, dual warm/cool light, clear air. "
    "The Tesla shape named above is large and recognizable, and it is the only subject. "
    "No second craft, no rocket, no satellite. Zero humans, no "
    "driver, no passengers, no faces. No logos, no readable text. Light architecture or "
    "realistic space, not a dark neon void, not a blown-up crop."
)

_SPACE_DC_LEAD = (
    "The hero is Starlink hardware as a data center in space. Flat rectangular satellite "
    "buses, each with one long solar wing. A field of them, or one satellite large and close. "
    "Earth is a real planet in the background. Not a building, not a server rack, not a user "
    "dish, not Falcon 9, not Starship."
)

_SPACE_DC_LOCK = (
    "Wide 16:9 cinematic CGI. Starlink satellites are the data center: flat rectangular "
    "buses, one long solar wing each. Earth is a real planet behind them. Neon is rim light "
    "on the panels. Not a server building, not racks, not a space station, not a user dish, "
    "not Falcon 9, not Starship. Zero humans, no logos, no readable text."
)

_SPACE_DC_SCENES = (
    "SCENE: a field of Starlink satellites, each a flat bus with one solar wing, spread as "
    "an orbital array. Earth large and real behind them. The array is the data center.",
    "SCENE: one Starlink satellite large and close, flat rectangular bus, one long solar "
    "wing, Earth filling the background. No second vehicle.",
    "SCENE: a train of identical Starlink satellites crossing the frame, Earth limb and "
    "clouds below, sun on the panels. Not a space station.",
    "SCENE: many Starlink satellites in a loose grid over the night side of Earth, city "
    "lights below, one satellite nearer and sharper. The constellation is the data center.",
)

# The failure mode on dBwghZT: a worm's-eye crop of one rib crossing, so the
# cathedral does not read as a building.
_CATHEDRAL_FRAME = (
    "The whole signal cathedral is in the frame and obvious. Floor, walls, and vault "
    "together, or the full dish tower from base to tip. Camera pulled back, with room "
    "around the building. You can tell what it is. Not a blown-up crop of one rib, joint, "
    "or window. Not a worm's-eye texture. Not a low angle gazing up into a single crossing."
)

_SIGNAL_CATHEDRAL_SCENES = (
    "SCENE: wide interior. The whole nave is visible, floor grating to the far vault, "
    "dish-arches readable as one cathedral. Camera pulled back. Not a crop of one rib.",
    "SCENE: the full hall in one glance, repeating arches small enough to count, stained "
    "neon panels, clear air. You can tell it is a signal hall. Not a macro.",
    "SCENE: exterior, the entire dish tower from the ground to the tip, off-center, sky "
    "around it. The tower is the subject. Not one dish filling the frame.",
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
    """Core skin plus older skins stored under that style. The core id stays the name.

    `iridescent` is a held material. It is not in this list, so the walk cannot pick it.
    """
    data = _raw()
    styles = data.get("styles") or {}
    val = styles.get(style_id) or {}
    extra = [
        k
        for k in (val.get("versions") or {})
        if k and k not in ("core", "iridescent")
    ]
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
        # A Tesla shape plate wears a clear backdrop. Count it as its own core
        # so it does not advance that backdrop's skin walk.
        if str(meta.get("story_core") or "") == "tesla-shape":
            out.append({"id": "tesla-shape", "version": sid})
        else:
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
    if chosen == "iridescent":
        over = {}
    elif chosen != "core":
        if chosen not in versions:
            raise ValueError(f"unknown version {chosen!r} of {key!r}; known: {version_ids(key)}")
        over = versions[chosen] or {}
    series = series_info()
    label = val.get("label", key)
    hashtag = val.get("hashtag") or _camel(label)
    notes = (over.get("art_director_notes") or val.get("art_director_notes") or "").strip()
    seed = (over.get("prompt_seed") or val.get("prompt_seed") or "").strip()
    if chosen == "iridescent":
        notes = f"{notes}\n{_IRIDESCENT_NOTES}".strip()
        seed = f"{seed} {_IRIDESCENT_LOCK}".strip()
    return {
        "id": key,
        "label": label,
        "description": val.get("description", ""),
        "hashtag": hashtag,
        "lane": (val.get("lane") or _LANE_DEFAULT).strip().lower(),
        "version": chosen,
        "version_scene": (over.get("scene") or "").strip(),
        "art_director_notes": notes,
        "prompt_seed": seed,
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


def shape_kind(text: str) -> str | None:
    """Cybertruck, Cybercab, an empty Tesla cabin, or Optimus at work.

    An explicit in-car phrase wins, then the named vehicle, then FSD as the cabin.
    """
    blob = text or ""
    if _CABIN_RE.search(blob) and _TESLA_CONTEXT_RE.search(blob):
        return "cabin"
    if _CYBERTRUCK_RE.search(blob):
        return "cybertruck"
    if _CYBERCAB_RE.search(blob):
        return "cybercab"
    if _ROBOT_RE.search(blob):
        return "robot"
    if _FSD_RE.search(blob):
        return "cabin"
    return None


def shape_lead(kind: str | None) -> str:
    return _SHAPE_LEAD.get(kind or "") or ""


def is_space_datacenter(text: str) -> bool:
    """Orbital compute and data centers in space. A ground data center is not this."""
    return bool(_SPACE_DC_RE.search(text or ""))


def _next_in(ids: tuple[str, ...] | list[str], last: str | None) -> str:
    if not ids:
        return ""
    if not last or last not in ids:
        return ids[0]
    return ids[(ids.index(last) + 1) % len(ids)]


def core_for_story(text: str) -> str:
    """Which core draws this story.

    Cybertruck, Cybercab, Optimus, and FSD cabins are the Tesla shape plates.
    A data center in space is Space DataCenter. Starship, Falcon 9, and
    Starlink satellites are Data Space, and the plate shows that object.
    Other space news is Planet Core. Nvidia and chip news are Rootkit City.
    AI news is Data Tunnel. Anything else is Signal Cathedral.
    """
    blob = text or ""
    if shape_kind(blob):
        return "tesla-shape"
    if is_space_datacenter(blob):
        return "space-datacenter"
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
        "space-datacenter": "space",
        "planet-core": "space",
        "data-tunnel": "ai",
        "tesla-shape": "ai",
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
    if core == "tesla-shape":
        if rng is not None:
            plate = rng.choice(_SHAPE_PLATES)
        else:
            looks = recent_looks() if recent is None else recent
            last = next((row["version"] for row in looks if row.get("id") == "tesla-shape"), None)
            plate = _next_in(_SHAPE_PLATES, last)
        style = get_style(plate, version="clear")
        style["shape"] = shape_kind(text)
        style["story_core"] = "tesla-shape"
        return style
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
    shape: str | None = None,
) -> str:
    """Composition hint for the art director — not appended to the Imagine prompt."""
    sid = str(style_id or "")
    key = salt or sid
    if shape and shape in _SHAPE_LEAD:
        plate = (version_scene or "").strip()
        return f"{_SHAPE_LEAD[shape]} {plate}".strip()
    hint = ""
    if version and version != "core" and version_scene:
        hint = version_scene.strip()
    elif sid in ("data-space", "data_space"):
        hint = _scene_pick(key, _DATA_SPACE_SCENES, "data-space")
    elif sid in ("space-datacenter", "space_datacenter"):
        hint = _scene_pick(key, _SPACE_DC_SCENES, "space-datacenter")
    elif sid in ("rootkit-city", "rootkit_city"):
        hint = _scene_pick(key, _ROOTKIT_CITY_SCENES, "rootkit-city")
    elif sid in ("signal-cathedral", "signal_cathedral"):
        hint = _scene_pick(key, _SIGNAL_CATHEDRAL_SCENES, "signal-cathedral")
    if sid in ("data-space", "data_space"):
        kind = vehicle or vehicle_kind(primary_line(salt))
        lead = _VEHICLE_LEAD.get(kind or "")
        if lead:
            hint = f"{lead} {hint}".strip()
    if sid in ("space-datacenter", "space_datacenter"):
        hint = f"{_SPACE_DC_LEAD} {hint}".strip()
    if sid in ("signal-cathedral", "signal_cathedral") and version != "clear":
        hint = f"{_CATHEDRAL_FRAME} {hint}".strip()
    if version == "iridescent":
        hint = f"{hint} {_IRIDESCENT_NOTES}".strip()
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



# Added skin only. The closer from the blue clear plates. Other versions do not use it.
_VFX_LOCK = (
    "Wide 16:9 finished VFX still. Photoreal materials, dual warm/cool light, "
    "atmospheric depth, epic scale. Zero humans. No logos or readable text. "
    "Neon accents subordinate to one hero structure. No lightning-bolt weather, "
    "no lava, no dark packed server-rack farm."
)

def _sanitize_cathedral_brief(brief: str) -> str:
    """A low angle into one joint is how the cathedral stops reading as a building."""
    if not brief:
        return brief
    replacements = (
        (r"\blow angle gazes up\b", "wide view shows"),
        (r"\bgazes up\b", "shows"),
        (r"\blooking up into\b", "looking across"),
        (r"\bworm'?s-?eye\b", "wide"),
        (r"\b(extreme|tight|macro)\s+close-?ups?\b", "wide view"),
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
    version = str(style.get("version") or "core")
    if style_id in ("signal-cathedral", "signal_cathedral") and version != "clear":
        shot = _sanitize_cathedral_brief(shot)

    shot_or_seed = shot or seed
    lead = shot_or_seed
    kind = None
    vehicle = ""
    shape = str(style.get("shape") or "")
    scene = (style.get("version_scene") or "").strip()
    older_scene = scene if scene and version not in ("", "core") else ""
    if style_id in ("data-space", "data_space"):
        kind = style.get("vehicle") or vehicle_kind(primary_line(source_text))
        vehicle = _VEHICLE_LEAD.get(kind or "")
        lead = "\n\n".join(part for part in (vehicle, older_scene, shot_or_seed) if part)
    elif older_scene:
        lead = "\n\n".join(part for part in (older_scene, shot_or_seed) if part)
    if version == "clear":
        # Added skin. Every other version keeps the lead and the lock below.
        plate = older_scene or seed
        shape_text = _SHAPE_LEAD.get(shape)
        if shape_text:
            lead = "\n\n".join(part for part in (shape_text, plate) if part)
            return "\n\n".join(part for part in (lead, _SHAPE_LOCK) if part)
        if style_id in ("space-datacenter", "space_datacenter"):
            lead = "\n\n".join(part for part in (_SPACE_DC_LEAD, plate) if part)
            return "\n\n".join(part for part in (lead, _VFX_LOCK) if part)
        if vehicle:
            lead = "\n\n".join(part for part in (vehicle, plate) if part)
        else:
            lead = plate
        return "\n\n".join(part for part in (lead, _VFX_LOCK) if part)
    if style_id in ("space-datacenter", "space_datacenter"):
        lead = "\n\n".join(part for part in (_SPACE_DC_LEAD, older_scene, shot_or_seed) if part)
        return "\n\n".join(part for part in (lead, _SPACE_DC_LOCK) if part)
    if style_id in ("signal-cathedral", "signal_cathedral"):
        lead = "\n\n".join(
            part for part in (_CATHEDRAL_FRAME, older_scene, shot_or_seed) if part
        )
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
        if style_id in ("signal-cathedral", "signal_cathedral"):
            lock += " The whole building stays in frame and stays obvious."
    if version == "iridescent":
        lock = f"{lock}\n\n{_IRIDESCENT_LOCK}"
    return "\n\n".join(p for p in (lead, lock) if p)
