"""Shared wire quality: visualizable events, fluff blocks, handle expansion.

Session 9 locked captions to source-only after a splashdown hallucination.
That trust bar stays. These helpers stop the *other* failure modes:

  - official brand tweets that are games / IR / academic marketing
  - @mention stripping that leaves 'the and ’s' holes
  - 220-char line clips that made posts look short
  - preferring a 1-line LAUNCH! over a fuller official clip
"""

from __future__ import annotations

import re

# Official handles we quote → display names (no @, so we do not notify on post).
_HANDLE_NAMES: dict[str, str] = {
    "spacex": "SpaceX",
    "nasa": "NASA",
    "nasaspaceflight": "NASASpaceflight",
    "nasakennedy": "NASA Kennedy",
    "esa": "ESA",
    "starlink": "Starlink",
    "nro_gov": "NRO",
    "nro": "NRO",
    "ussf_ssc": "USSF",
    "ussf": "USSF",
    "xai": "xAI",
    "tesla": "Tesla",
    "elonmusk": "Elon Musk",
    "openai": "OpenAI",
    "anthropicai": "Anthropic",
    "googledeepmind": "Google DeepMind",
    "metaai": "Meta AI",
    "sama": "Sam Altman",
    "nvidia": "NVIDIA",
    "nvidiaai": "NVIDIA",
    "nvidiageforce": "NVIDIA",
}

# Brand-account fluff that passed the old primary-only bonus.
# Games (NVIDIA GeForce), IR tools (Tesla earnings Qs), academic marketing (OpenAI).
_FLUFF_RE = re.compile(
    r"("
    r"gears of war|call of duty|fortnite|valorant|cyberpunk|"
    r"horde siege|\b4v4\b|open beta|\bversus\b|"
    r"dlss super|#?rtx\s*on\b|"
    r"earnings webcast|earnings call|investors can submit|submit questions|"
    r"ahead of our (first )?earnings|"
    r"academic researchers|chatgpt for academic|"
    r"free access to (our )?frontier|"
    r"\b\d{1,3},?\d{3} researchers\b|"
    r"photo of the day|picture of the day|image of the day|"
    r"looks absolutely|stunning photos?|don'?t miss these|you may like|"
    r"giveaway|enter to win|win this|free pc drop|pc drop|"
    r"steigerdynamics|#?rtxpowersplay|"
    r"air show|aerospace technology expo|make plans to join us|"
    r"responsible scaling policy|risk reports?"
    r")",
    re.I,
)

# A real event the series can metaphorize — not "brand tweeted today".
# Brands themselves are NOT events (NVIDIA posting a game ad still says NVIDIA).
# The last group is the Signal Cathedral material: a car, a plant, an approval.
# Those stories do not say launch, chip, or FSD, and the old pattern dropped them.
_EVENT_RE = re.compile(
    r"\b("
    r"launch(?:es|ed|ing)?|landing|landed|splashdown|orbit(?:al|s)?|"
    r"deploys?|deployed|flight\s+test|starlink\s+group|"
    r"falcon|starship|booster|crew\s+dragon|super\s+heavy|raptor|"
    r"gpu|gpus|blackwell|rubin|nvl\d+|h100|h200|b100|b200|gb200|"
    r"silicon|wafer|chip|cpu|compute\s+tray|tensor\s+core|ai\s+chip|"
    r"gpt-?\d|grok[- ]?\d|open[- ]?weights|"
    r"model\s+(release|launch|weights|checkpoint)|"
    r"optimus|dojo|robo-?taxis?|\bfsd\b|full\s+self[- ]?driving|self[- ]driving|"
    r"unveils?|unveiled|now\s+available|"
    r"plans?|planned|plant|factory|gigafactory|"
    r"cybercabs?|cybertrucks?|roadster|steering\s+wheel|"
    r"model\s*[ysx3]\b|"
    r"approv(?:e|es|ed|al)|green\s+light|"
    r"orders?|deliver(?:y|ies|ed)|production|polysilicon|solar\s+roof"
    r")\b",
    re.I,
)

# Cool-tech words that are still not a plate: a crash, a quote page, a roundup.
_OFF_PLATE_RE = re.compile(
    r"\b("
    r"duis?|crashes\s+into|killed|critically\s+(?:injured|hurt)|"
    r"catches\s+fire|caught\s+fire|car\s+fire|"
    r"stock\s+price|share\s+price|shareholders|institutions\s+held|"
    r"buying\s+guide|top\s+stories|this\s+week\s+in|"
    r"mergers?|\bipo\b"
    r")\b",
    re.I,
)

_HANDLE_RE = re.compile(r"@(\w+)('s|’s|′s)?")


def expand_handles(text: str) -> str:
    """Turn @NRO_gov / @USSF_SSC's into NRO / USSF's. Never leave grammar holes.

    Unknown handles keep the word without @ (still no notification on post).
    """

    def _repl(m: re.Match[str]) -> str:
        handle = m.group(1)
        poss = m.group(2) or ""
        name = _HANDLE_NAMES.get(handle.lower(), handle)
        return name + poss

    out = _HANDLE_RE.sub(_repl, text or "")
    return re.sub(r"\s+", " ", out).strip()


def is_fluff(text: str) -> bool:
    return bool(_FLUFF_RE.search(text or ""))


def is_visualizable_event(text: str) -> bool:
    return bool(_EVENT_RE.search(text or ""))


def wire_accept(text: str) -> bool:
    """True if this clip can be the Planet Hack story."""
    t = (text or "").strip()
    if len(t) < 24:
        return False
    if is_fluff(t) or _OFF_PLATE_RE.search(t):
        return False
    return is_visualizable_event(t)


def viral_word_bonus(text: str) -> int:
    """A quoted line and a concrete figure are the words a plate should lead with."""
    t = text or ""
    score = 0
    if re.search(r"[\"“”‘’«»]", t):
        score += 28
    if re.search(r"\$\d|\b\d{3,}\b", t):
        score += 12
    return score


def length_bonus(n: int) -> int:
    """Prefer a full official sentence over a 1-line LAUNCH! when both exist."""
    if 90 <= n <= 280:
        return 18
    if 60 <= n < 90:
        return 8
    if 40 <= n < 60:
        return 0
    if n < 40:
        return -12
    # 280+ still fine (we clip later); don't punish a long official post
    return 10


def longest_source_text(item: dict) -> str:
    """Pick the longest wire string — never a 160/220 display truncate."""
    title = (item.get("title") or "").strip()
    summary = re.sub(r"https?://\S+", "", (item.get("summary") or "").strip())
    summary = re.sub(r"\s+", " ", summary).strip()
    line = re.sub(r"https?://\S+", "", (item.get("line") or "").strip())
    line = re.sub(r"\s+", " ", line).strip()
    full = re.sub(r"https?://\S+", "", (item.get("text") or "").strip())
    full = re.sub(r"\s+", " ", full).strip()

    combo = ""
    if title and summary and summary.lower() not in title.lower():
        combo = f"{title} — {summary}"

    candidates = [full, line, combo, title]
    body = max(candidates, key=len)
    return expand_handles(body)
