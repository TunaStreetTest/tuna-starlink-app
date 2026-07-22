"""X recent search for Planet Hack — real headlines over viral junk.

Session 2 fix: Free-tier keyword search returns study logs, crypto promos, and
meme "Breaking" posts. We prefer (1) known news accounts, (2) has:links newsy
queries, then rank with strict junk filters + headline-likeness.

Cost guard (2026-07): X Recent Search is paid. Defaults:
  - X_SEARCH_ENABLED=false (kill switch)
  - per-lane TTL cache so peak-window runs share one lookup
  - stop after first query that fills keepers (outlet query first)
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

# Per lane: list of queries tried in order until we have enough keepers.
# Outlet accounts first (high signal), then keyword + has:links.
_LANE_QUERIES: dict[str, list[str]] = {
    "geopolitics": [
        (
            "(from:Reuters OR from:AP OR from:BBCWorld OR from:AJEnglish OR from:NPR "
            "OR from:guardian OR from:SkyNews OR from:dwnews) "
            "-is:retweet -is:reply lang:en"
        ),
        (
            "(breaking OR war OR ceasefire OR sanctions OR election OR NATO OR Iran "
            "OR Ukraine OR Gaza OR China OR Russia) has:links "
            "-is:retweet -is:reply lang:en"
        ),
    ],
    "tech": [
        (
            "(from:Reuters OR from:BBCTech OR from:verge OR from:WIRED OR from:TechCrunch "
            "OR from:arstechnica OR from:TheRegister) "
            "-is:retweet -is:reply lang:en"
        ),
        (
            "(OpenAI OR NVIDIA OR Apple OR Google OR Microsoft OR semiconductor OR cyber "
            "OR \"artificial intelligence\") (announces OR announced OR reports OR reported "
            "OR launches OR launched OR breach OR lawsuit) has:links "
            "-is:retweet -is:reply lang:en"
        ),
    ],
    "science": [
        (
            "(from:NASA OR from:Nature OR from:ScienceMagazine OR from:BBCScienceNews "
            "OR from:Space_Station OR from:ESA OR from:ReutersScience) "
            "-is:retweet -is:reply lang:en"
        ),
        (
            "(NASA OR climate OR fusion OR quantum OR wildfire OR earthquake OR vaccine "
            "OR telescope OR mars OR scientists) (reports OR discovered OR announces "
            "OR study OR research) has:links -is:retweet -is:reply lang:en"
        ),
    ],
    "markets": [
        (
            "(from:ReutersBiz OR from:WSJ OR from:FT OR from:Bloomberg OR from:CNBC "
            "OR from:markets OR from:TheEconomist) "
            "-is:retweet -is:reply lang:en"
        ),
        (
            "(tariff OR Fed OR inflation OR stocks OR \"interest rate\" OR GDP OR recession "
            "OR earnings OR \"oil price\") (rises OR falls OR announces OR reports OR beats "
            "OR misses) has:links -is:retweet -is:reply lang:en"
        ),
    ],
}

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

# Post-filter outlet results so geopolitics doesn't lead with Alphabet earnings.
_LANE_MATCH: dict[str, tuple[str, ...]] = {
    "geopolitics": (
        "war", "ceasefire", "sanction", "diplomat", "election", "nato", "military",
        "invasion", "treaty", "president", "minister", "border", "missile", "ukraine",
        "israel", "gaza", "iran", "china", "russia", "congress", "senate", "un ",
        "security council", "troops", "strike", "hostage", "summit", "protest",
        "refugee", "ice ", "immigration", "governor", "prime minister", "pentagon",
        "white house", "state department", "foreign", "embassy", "coup", "ballot",
    ),
    "tech": (
        "ai ", "artificial intelligence", "chip", "semiconductor", "cyber", "hack",
        "software", "openai", "google", "apple", "microsoft", "nvidia", "gpu",
        "startup", "internet", "crypto", "bitcoin", "robot", "cloud", "alphabet",
        "meta ", "amazon", "iphone", "android", "data center", "model", "llm",
        "tech", "app ", "smartphone", "quantum computing",
    ),
    "science": (
        "nasa", "space", "climate", "energy", "fusion", "quantum", "research",
        "scientist", "storm", "wildfire", "earthquake", "virus", "vaccine",
        "telescope", "mars", "ocean", "species", "physics", "ebola", "nuclear",
        "heatwave", "hurricane", "earth", "biology", "genome", "cancer", "study",
        "astronaut", "orbit", "reef", "emissions", "temperature",
    ),
    "markets": (
        "market", "stock", "tariff", "fed ", "inflation", "bank", "trade",
        "gdp", "recession", "bond", "dollar", "oil", "layoff", "earnings",
        "wall street", "economy", "revenue", "shares", "nasdaq", "dow ",
        "s&p", "interest rate", "jobs report", "unemployment", "price",
        "ipo", "merger", "acquisition", "quarterly",
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


def _run_query(client: Any, query: str, max_results: int) -> list[dict[str, Any]]:
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
        if _is_junk(text):
            continue
        score = _quality_score(text, likes, rts, replies, quotes)
        if score < _MIN_SCORE:
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
    """Search a lane via outlet + keyword queries; return ranked keepers.

    No-ops when X_SEARCH_ENABLED=false. Uses per-lane TTL cache unless
    bypass_cache=True.
    """
    if not search_enabled():
        log.info("X search skipped (X_SEARCH_ENABLED=false)")
        return []

    lane = (lane or "geopolitics").lower().strip()
    if not bypass_cache:
        cached = _cache_get(lane)
        if cached is not None:
            log.info(
                "X search cache hit lane=%s kept=%s",
                lane,
                len(cached),
            )
            return cached[:_MAX_KEEP_PER_SEARCH]

    queries = _LANE_QUERIES.get(lane) or _LANE_QUERIES["geopolitics"]
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
        batch = _run_query(client, query, max_results=max_results)
        queries_run += 1
        for hit in batch:
            text = hit.get("text") or hit.get("line") or ""
            # Outlet timelines mix topics — keep only on-lane headlines
            if not _matches_lane(text, lane):
                continue
            hit["lane"] = lane
            hit["query_rank"] = i  # 0 = preferred outlet query
            if i == 0:
                hit["score"] = int(hit.get("score") or 0) + 15
            tid = hit.get("id") or ""
            if not tid:
                continue
            prev = by_id.get(tid)
            if not prev or hit["score"] > prev["score"]:
                by_id[tid] = hit
        # Cost: one billable search is enough when outlet query yields keepers.
        # Keyword fallback only runs if query 0 produced nothing on-lane.
        if len(by_id) >= 1:
            break

    out = sorted(by_id.values(), key=lambda x: x["score"], reverse=True)
    out = out[:_MAX_KEEP_PER_SEARCH]
    _cache_set(lane, out)
    log.info(
        "X search lane=%s queries_run=%s kept=%s top_score=%s ttl_m=%s",
        lane,
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
