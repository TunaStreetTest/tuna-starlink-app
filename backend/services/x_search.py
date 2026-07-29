"""X recent search for Planet Hack — primary brand posts over secondary rewrite.

Prefer official accounts (SpaceX, Tesla, NVIDIA, xAI, OpenAI, …) so we quote
the primary source, not "space photo of the day" Google News rewrites.

Cost guard: X Recent Search is paid.
  - X_SEARCH_ENABLED kill switch (default off in config; enable when you want wire)
  - X_SEARCH_PRIMARY_ONLY=true → one official-account query per lane, then stop
  - per-lane TTL cache so runs share one lookup
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from config import settings

log = logging.getLogger("tuna-starlink.x_search")

# lane -> (expires_monotonic, hits)
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}

# Official brand handles — primary source, not a desk rewrite.
_PRIMARY_SPACE = (
    "from:SpaceX OR from:NASA OR from:NASASpaceflight OR from:NASAKennedy "
    "OR from:esa OR from:Starlink"
)
_PRIMARY_AI = (
    "from:xai OR from:Tesla OR from:elonmusk OR from:OpenAI OR from:AnthropicAI "
    "OR from:GoogleDeepMind OR from:MetaAI OR from:sama"
)
_PRIMARY_GPU = (
    "from:nvidia OR from:NVIDIAAI OR from:NVIDIAGeForce OR from:OpenAI OR from:AnthropicAI"
)

# Per lane: primary accounts first (stop after keepers when PRIMARY_ONLY).
# Cool-tech lanes (space/ai/gpu) are what Planet Hack styles use.
_LANE_QUERIES: dict[str, list[str]] = {
    "space": [
        f"({_PRIMARY_SPACE}) -is:retweet -is:reply lang:en",
        (
            "(SpaceX OR Starship OR Starlink OR Falcon) (launch OR launches OR launched "
            "OR flight OR splashdown OR orbit OR deploy OR test) has:links "
            "-is:retweet -is:reply lang:en"
        ),
    ],
    "ai": [
        f"({_PRIMARY_AI}) -is:retweet -is:reply lang:en",
        (
            "(xAI OR Grok OR Tesla OR Optimus OR OpenAI OR Anthropic OR LLM) "
            "(announce OR announces OR announced OR release OR launches OR launched) has:links "
            "-is:retweet -is:reply lang:en"
        ),
    ],
    "gpu": [
        f"({_PRIMARY_GPU}) -is:retweet -is:reply lang:en",
        (
            "(NVIDIA OR Blackwell OR H100 OR B200 OR GB200 OR GPU) "
            "(announce OR announces OR shipping OR launch) has:links "
            "-is:retweet -is:reply lang:en"
        ),
    ],
    # legacy aliases → same cool-tech primary desks
    "science": [
        f"({_PRIMARY_SPACE}) -is:retweet -is:reply lang:en",
    ],
    "tech": [
        f"({_PRIMARY_AI} OR {_PRIMARY_GPU}) -is:retweet -is:reply lang:en",
    ],
    "markets": [
        f"({_PRIMARY_GPU}) -is:retweet -is:reply lang:en",
    ],
    "geopolitics": [
        f"({_PRIMARY_SPACE}) -is:retweet -is:reply lang:en",
    ],
}

# Soft junk still common on free keyword search
_SOFT_FEATURE_RE = re.compile(
    r"("
    r"photo of the day|picture of the day|image of the day|"
    r"looks absolutely|stunning photos?|don'?t miss these|"
    r"you may like|watch this space"
    r")",
    re.I,
)

_JUNK_RE = re.compile(
    r"("
    r"day\s*[:#]?\s*\d+\s+of\b|"
    r"\b(learnt|learned|potd|leetcode|cp-31|grind|becoming better)\b|"
    r"\b(follow\s+me|link\s+in\s+bio|subscribe|giveaway|dm\s+me)\b|"
    r"\b(paid\s+discord|enroll|clinical\s+research|compensation\s+for)\b|"
    r"\b(newest\s+course|course\s+is\s+built|sign\s+up)\b|"
    r"\b(investing\s+vs\s+trading|pick\s+yours\s+and\s+commit)\b|"
    r"\b(top\s+5\s+gainers|rsi\s+\d|low\s+cap|real\s+gems)\b|"
    r"\b(robinhoodapp|seed phrase|no app\. no seed)\b|"
    r"\b(tokenized|perp\b|memes?|\$[A-Z]{2,5}\b.*\$[A-Z]{2,5})\b|"
    r"\b(launch your own|in 60 seconds|hold the token)\b|"
    r"\b(2nd half|offense|wnba|nba|mlb|nfl|goalie|touchdown|transfer window)\b|"
    r"\b(aivideo|ai\s*video)\b|"
    r"(✅|💯|✨|😄|🏆|🚀){2,}|"
    r"\b(i\s+just\s+finished|my\s+progress|daily\s+update)\b|"
    # viral junk that scored high previously
    r"\b(jimothy|frog-like|spotting this morning|watch until the end)\b|"
    r"\b(tug of war with taffy|i fear ai more)\b|"
    r"\b(please join us|register here|technical working group)\b|"
    r"\b(episode\s+\d+|is\s+live!|topics for today)\b|"
    r"\b(i thought i knew|i'm shocked by|beyond disgusting)\b|"
    r"\b(bullish news for|i expect big up move)\b"
    r")",
    re.I,
)

_NEWSY_RE = re.compile(
    r"\b(breaking|announces|announced|reports|reported|says|said|"
    r"official|war|tariff|sanctions|launch|launched|breach|attack|"
    r"climate|storm|wildfire|election|ceasefire|inflation|fed|"
    r"killed|dies|dead|strike|deal|court|indict|resign|"
    r"discovered|study|researchers?|earnings|revenue|gdp)\b",
    re.I,
)

# First-person diary / opinion fluff (not a wire headline)
_OPINION_RE = re.compile(
    r"^(i |i'm |im |we |my |our |you |this is beyond|i thought|i fear|"
    r"please |avoiding war is not|it makes you)",
    re.I,
)

_MIN_TEXT = 50
_MIN_SCORE = 35  # raise bar so "Breaking Jimothy" style trash drops out
_MAX_KEEP_PER_SEARCH = 8

# Keyword-fallback only — primary account hits skip this filter.
_LANE_MATCH: dict[str, tuple[str, ...]] = {
    "space": (
        "spacex", "starship", "starlink", "falcon", "rocket", "launch", "orbit",
        "splashdown", "nasa", "mars", "satellite", "crew dragon", "super heavy",
        "raptor", "starbase", "booster", "capsule", "flight test",
    ),
    "ai": (
        "ai ", "artificial intelligence", "openai", "anthropic", "claude", "chatgpt",
        "gpt", "grok", "xai", "llm", "model", "tesla", "optimus", "dojo", "fsd",
        "robotaxi", "deepmind", "mistral", "llama", "open weights",
    ),
    "gpu": (
        "nvidia", "gpu", "h100", "h200", "b100", "b200", "blackwell", "hopper",
        "cuda", "chip", "semiconductor", "accelerator", "gb200", "inference",
        "data center", "datacenter", "tpu",
    ),
    # legacy aliases
    "tech": (
        "ai ", "openai", "nvidia", "gpu", "tesla", "xai", "grok", "llm", "chip",
    ),
    "science": (
        "spacex", "starship", "nasa", "orbit", "launch", "rocket", "mars",
    ),
    "markets": (
        "nvidia", "gpu", "chip", "semiconductor", "datacenter", "earnings",
    ),
    "geopolitics": (
        "spacex", "starship", "nasa", "orbit", "launch",
    ),
}


def _client():
    import tweepy

    if not all(
        [
            settings.X_API_KEY,
            settings.X_API_SECRET,
            settings.X_ACCESS_TOKEN,
            settings.X_ACCESS_TOKEN_SECRET,
        ]
    ):
        raise RuntimeError("X credentials incomplete for search")
    return tweepy.Client(
        consumer_key=settings.X_API_KEY,
        consumer_secret=settings.X_API_SECRET,
        access_token=settings.X_ACCESS_TOKEN,
        access_token_secret=settings.X_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=False,
    )


def _clean_line(text: str) -> str:
    t = (text or "").replace("\n", " ").strip()
    t = t.replace("&gt;", ">").replace("&amp;", "&").replace("&lt;", "<")
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    # strip trailing media-only residue
    t = re.sub(r"\s*[|•]\s*$", "", t)
    return t


def _matches_lane(text: str, lane: str) -> bool:
    """Outlet feeds mix topics — drop off-lane posts (e.g. Alphabet in geopolitics)."""
    blob = f" {((text or '').lower())} "
    kws = _LANE_MATCH.get(lane) or ()
    if not kws:
        return True
    return any(kw in blob for kw in kws)


def _is_junk(text: str) -> bool:
    t = text or ""
    if len(t) < _MIN_TEXT:
        return True
    if _JUNK_RE.search(t):
        return True
    if _SOFT_FEATURE_RE.search(t):
        return True
    if _OPINION_RE.search(t.strip()):
        return True
    if t.count("->") + t.count("→") + t.count("-&gt;") >= 3:
        return True
    # pure stock ticker spam
    if len(re.findall(r"\$[A-Z]{1,5}", t)) >= 3 and not _NEWSY_RE.search(t):
        return True
    # emoji-heavy hype
    emojiish = len(re.findall(r"[\U0001F300-\U0001FAFF]", t))
    if emojiish >= 4:
        return True
    # too many @ mentions = not a headline
    if t.count("@") >= 3:
        return True
    return False


def _headline_bonus(text: str) -> int:
    """Reward posts that read like wire headlines, not threads or ads."""
    t = (text or "").strip()
    score = 0
    if _NEWSY_RE.search(t):
        score += 20
    if re.search(r"\b(BREAKING|Breaking)\b", t):
        # only if also newsy body — bare "BREAKING:" can be meme bait
        if _NEWSY_RE.search(t) and not re.search(r"spotting|frog|watch until", t, re.I):
            score += 12
    n = len(t)
    if 55 <= n <= 220:
        score += 12
    elif 40 <= n < 55 or 220 < n <= 280:
        score += 6
    # declarative title shape: starts with capital letter/word, few first-person
    if re.match(r"^[A-Z\"“']", t) and not re.search(r"\bI\b", t[:40]):
        score += 8
    # has numbers / proper-noun density hint (earnings, deaths, etc.)
    if re.search(r"\b\d{1,4}([.,]\d+)?%?\b", t):
        score += 5
    # penalize question-only engagement bait
    if t.count("?") >= 2:
        score -= 10
    if t.count("#") >= 4:
        score -= 10
    return score


def _quality_score(text: str, likes: int, rts: int, replies: int, quotes: int) -> int:
    eng = likes + 2 * rts + quotes + replies
    # engagement is nice but Free tier often returns 0 — don't rely on it alone
    return min(eng * 2, 40) + _headline_bonus(text)


def _run_query(
    client: Any, query: str, max_results: int, *, primary: bool = False
) -> list[dict[str, Any]]:
    try:
        resp = client.search_recent_tweets(
            query=query,
            max_results=max_results,
            tweet_fields=["public_metrics", "created_at", "lang"],
            user_auth=True,
        )
    except Exception as e:
        log.warning("X search query failed: %s — %s", query[:60], e)
        return []

    data = getattr(resp, "data", None) or []
    out: list[dict[str, Any]] = []
    # Official accounts often post short operational updates — keep them.
    min_text = 24 if primary else _MIN_TEXT
    min_score = 15 if primary else _MIN_SCORE
    for tw in data:
        metrics = getattr(tw, "public_metrics", None) or {}
        if isinstance(metrics, dict):
            likes = int(metrics.get("like_count") or 0)
            rts = int(metrics.get("retweet_count") or 0)
            replies = int(metrics.get("reply_count") or 0)
            quotes = int(metrics.get("quote_count") or 0)
        else:
            likes = rts = replies = quotes = 0
        text = _clean_line(getattr(tw, "text", None) or "")
        if len(text) < min_text:
            continue
        # Soft features still junk; other junk filters softer on primary
        if _SOFT_FEATURE_RE.search(text):
            continue
        if not primary and _is_junk(text):
            continue
        if primary and _OPINION_RE.search(text.strip()):
            continue
        score = _quality_score(text, likes, rts, replies, quotes)
        if primary:
            score += 25  # brand voice is the product
        if score < min_score:
            continue
        tid = str(getattr(tw, "id", "") or "")
        out.append(
            {
                "id": tid,
                "text": text,
                "line": text[:220],
                "title": text[:160],
                "score": score,
                "likes": likes,
                "retweets": rts,
                "url": f"https://x.com/i/web/status/{tid}" if tid else "",
                "source": "x-search",
                "created_at": str(getattr(tw, "created_at", "") or ""),
                "primary_account": primary,
            }
        )
    return out


def search_enabled() -> bool:
    return bool(settings.X_SEARCH_ENABLED) and not settings.DRY_RUN


def cache_stats() -> dict[str, Any]:
    now = time.monotonic()
    live = {k: len(v[1]) for k, v in _CACHE.items() if v[0] > now}
    return {
        "enabled": search_enabled(),
        "ttl_minutes": int(settings.X_SEARCH_TTL_MINUTES or 0),
        "max_results": int(settings.X_SEARCH_MAX_RESULTS or 10),
        "lanes_cached": list(live.keys()),
        "hits_by_lane": live,
    }


def _cache_get(lane: str) -> list[dict[str, Any]] | None:
    ttl = max(0, int(settings.X_SEARCH_TTL_MINUTES or 0))
    if ttl <= 0:
        return None
    entry = _CACHE.get(lane)
    if not entry:
        return None
    expires, hits = entry
    if time.monotonic() >= expires:
        _CACHE.pop(lane, None)
        return None
    # return shallow copies so callers can't mutate the cache
    return [dict(h) for h in hits]


def _cache_set(lane: str, hits: list[dict[str, Any]]) -> None:
    ttl = max(0, int(settings.X_SEARCH_TTL_MINUTES or 0))
    if ttl <= 0:
        return
    _CACHE[lane] = (time.monotonic() + ttl * 60, [dict(h) for h in hits])


def search_lane(
    lane: str, max_results: int | None = None, *, bypass_cache: bool = False
) -> list[dict[str, Any]]:
    """Search a lane via primary accounts (+ optional keyword); return ranked keepers.

    No-ops when X_SEARCH_ENABLED=false. Uses per-lane TTL cache unless
    bypass_cache=True. When X_SEARCH_PRIMARY_ONLY, only the first (official
    account) query runs — cheaper and higher trust.
    """
    if not search_enabled():
        log.info("X search skipped (X_SEARCH_ENABLED=false)")
        return []

    lane = (lane or "space").lower().strip()
    # Map leftovers onto cool-tech
    if lane in ("science", "geopolitics"):
        lane = "space"
    elif lane in ("tech",):
        lane = "ai"
    elif lane in ("markets",):
        lane = "gpu"

    if not bypass_cache:
        cached = _cache_get(lane)
        if cached is not None:
            log.info(
                "X search cache hit lane=%s kept=%s",
                lane,
                len(cached),
            )
            return cached[:_MAX_KEEP_PER_SEARCH]

    queries = list(_LANE_QUERIES.get(lane) or _LANE_QUERIES["space"])
    primary_only = bool(getattr(settings, "X_SEARCH_PRIMARY_ONLY", True))
    if primary_only:
        queries = queries[:1]

    if max_results is None:
        max_results = int(settings.X_SEARCH_MAX_RESULTS or 10)
    # X API min for recent search is 10
    max_results = max(10, min(int(max_results), 25))

    try:
        client = _client()
    except Exception as e:
        log.warning("X client unavailable: %s", e)
        return []

    by_id: dict[str, dict[str, Any]] = {}
    queries_run = 0
    for i, query in enumerate(queries):
        is_primary = i == 0
        batch = _run_query(client, query, max_results=max_results, primary=is_primary)
        queries_run += 1
        for hit in batch:
            text = hit.get("text") or hit.get("line") or ""
            # Keyword fallback still needs on-lane filter; primary accounts are trusted
            if not is_primary and not _matches_lane(text, lane):
                continue
            hit["lane"] = lane
            hit["query_rank"] = i  # 0 = preferred primary accounts
            hit["primary_account"] = is_primary or bool(hit.get("primary_account"))
            if is_primary:
                hit["score"] = int(hit.get("score") or 0) + 40  # strong primary boost
            tid = hit.get("id") or ""
            if not tid:
                continue
            prev = by_id.get(tid)
            if not prev or hit["score"] > prev["score"]:
                by_id[tid] = hit
        # Cost: stop after first query that yields keepers (primary-first).
        if len(by_id) >= 1:
            break

    out = sorted(by_id.values(), key=lambda x: x["score"], reverse=True)
    out = out[:_MAX_KEEP_PER_SEARCH]
    _cache_set(lane, out)
    log.info(
        "X search lane=%s primary_only=%s queries_run=%s kept=%s top_score=%s ttl_m=%s",
        lane,
        primary_only,
        queries_run,
        len(out),
        out[0]["score"] if out else 0,
        settings.X_SEARCH_TTL_MINUTES,
    )
    return out


def pick_best_story(lane: str) -> dict[str, Any] | None:
    hits = search_lane(lane)
    if not hits:
        return None
    return hits[0]


def pick_top_stories(lane: str, n: int = 2) -> list[dict[str, Any]]:
    """Top N distinct X headlines for multi-source packs."""
    hits = search_lane(lane)
    if not hits:
        return []
    # light de-dupe by first 48 chars
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for h in hits:
        key = re.sub(r"\W+", "", (h.get("line") or "")[:48].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
        if len(out) >= n:
            break
    return out
