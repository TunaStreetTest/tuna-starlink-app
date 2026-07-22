# TunaStarLink App — Planet Hack

World headlines → **news stream tap** → **Grok art director** → **xAI Imagine** → gallery → **@tunastarlink** on X.

Series look: hacker-movie **3D digital cyberspace / hacking the planet**.  
Home host: **Beelink SER9 (`TunaStarlink`)** on Starlink (also runs fine on a laptop).

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app

---

## Product

Each run:

1. **Ingest** public RSS into a local news stream (`art/.news_stream.json`)
2. **Wire pack** — X search (news outlets / headlines) + RSS for the style's news lane → ~3 headlines
3. **Art director** (Grok) metaphors the **primary** story into a visual brief
4. **Imagine** (`grok-imagine-image`, ~$0.02, landscape 16:9)
5. **Caption** + save `art/<run_id>/art.png` + `meta.json`
6. **X post** (manual or `AUTO_PUBLISH`) — mood caption on main; **Generative Stream** reply carries the wire (full ~280)

Downloads: `planethack_<run_id>.png`.

### Styles

| id | Shot |
|---|---|
| `planet-core` | Planetary mainframe core |
| `data-tunnel` | Packet tunnel flythrough |
| `signal-cathedral` | Signal megastructure (wide landscape) |
| `rootkit-city` | Circuit metropolis mid-infiltration |

Peak schedule (**7–10pm ET**, every **21m**) picks a style at random. Studio dropdown for manual runs.  
Share new styles: [`docs/STYLE-SEEDS.md`](docs/STYLE-SEEDS.md).

---

## Quick start

```bash
cd ~/tuna-starlink-app
cp backend/.env.example backend/.env.local
# fill keys — see .env section below

make backend     # http://127.0.0.1:8010
make frontend    # http://127.0.0.1:5174  (proxies /api → :8010)
```

Zero-cost plumbing test:

```bash
make dry-run
```

Docker:

```bash
# put the same vars in .env next to docker-compose.yml
docker compose up --build
# http://127.0.0.1:8091
```

Beelink install: [`docs/BEELINK-INSTALL.md`](docs/BEELINK-INSTALL.md).

---

## Full `.env` / `backend/.env.local`

```env
# --- generation ---
DRY_RUN=false
ART_STORAGE_PATH=../art

XAI_API_KEY=xai-...
XAI_CHAT_MODEL=grok-4-1-fast-reasoning
XAI_IMAGE_MODEL=grok-imagine-image
XAI_IMAGE_SIZE=1792x1024
XAI_IMAGE_ASPECT_RATIO=16:9

DEFAULT_STYLE=data-tunnel
EVENTS_SOURCE=stream

# optional local text model on Beelink
EDGE_TEXT=xai
LEMONADE_URL=http://127.0.0.1:13305
LEMONADE_MODEL=Qwen3-4B-GGUF

# --- unattended ---
SCHEDULE_ENABLED=true
SCHEDULE_INTERVAL_MINUTES=21
SCHEDULE_TIMEZONE=America/New_York
SCHEDULE_CRON=peak 19:00-22:59 every 21m
AUTO_PUBLISH=true

# --- X / @tunastarlink (OAuth 1.0a) ---
# API key/secret = developer app (can be the same project as other bots).
# Access token/secret MUST be for @tunastarlink (not another account).
X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=
X_ACCOUNT_HANDLE=@tunastarlink
```

OAuth pin helper (authorize @tunastarlink under your developer app):

```bash
# start flow prints a URL — log into X as @tunastarlink, authorize, get PIN
# then:
python scripts/x-oauth-finish.py <PIN>
```

That writes access tokens into `backend/.env.local`. Restart the backend after any env change.

---

## X (@tunastarlink)

| Step | Content |
|---|---|
| Main | Image + atmospheric caption + `#PlanetHack #DataTunnel` (style camelCase) |
| One reply | `Generative Stream: <wire headlines> #DataTunnel` — real news payload, uses most of 280 |

Stored on each run: `x_url`, `x_post_id`, `x_replies`, `stream_slug`, `events_source` in `meta.json`.

**Gallery** tab → tile → modal → **Post to X**, or enable `AUTO_PUBLISH=true` for peak auto-post.

---

## Overnight

```env
SCHEDULE_ENABLED=true
SCHEDULE_INTERVAL_MINUTES=21
SCHEDULE_TIMEZONE=America/New_York
SCHEDULE_CRON=peak 19:00-22:59 every 21m
AUTO_PUBLISH=true
EVENTS_SOURCE=stream
```

Leave backend or Docker running. ~$0.02–0.04 xAI per fire (~9–12 fires if the full peak window runs).

---

## API

| Method | Path | |
|---|---|---|
| GET | `/api/health` | disk, xAI, X |
| GET | `/api/styles` | style list |
| POST | `/api/generate` | `{ "style": "data-tunnel", "wait": false }` |
| GET | `/api/pipeline` | current run + news stream stats |
| GET | `/api/gallery` | runs |
| GET | `/api/gallery/{id}/image` | PNG (`planethack_<id>.png`) |
| GET | `/api/publish/status` | X credentials ready? |
| POST | `/api/publish/x` | `{ "run_id": "…", "with_comments": true }` |
| POST | `/api/publish/x/reply` | repair news comment |

```bash
DRY_RUN=1 ART_STORAGE_PATH=./art python worker/run_once.py --style data-tunnel
```

---

## Build stats (whole repo)

Two Grok Build sessions (same conversation continued), model **grok-4.5**.  
Index + method: [`docs/STATS.md`](docs/STATS.md) · Session 1: [`docs/STATS-SESSION-1.md`](docs/STATS-SESSION-1.md) · Session 2: [`docs/STATS-SESSION-2.md`](docs/STATS-SESSION-2.md).

### Lines of code (current repo)

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **2,675** |
| Frontend (`frontend/src`) | **1,147** |
| Style seeds + compose YAML | **112** |
| **Application code** | **~3,934** |
| Docs (`docs/`, README, GROK) | **1,277** |
| Makefile / Dockerfile / `.env.example` / samples | **119** |
| **All product files** | **~5,330** |

(Excludes `node_modules`, `.venv`, generated `art/`, lockfiles.) Session 1 ended ~3.1k app / ~4.0k product; Session 2 added ~**+800** app / ~**+1.3k** product.

### Combined session activity (S1 + S2)

| Metric | Value |
|---|---:|
| Active engineering time (S1 + S2) | **~5.2 hours** (excludes overnight idle) |
| User turns | **60** |
| Assistant messages | **249** |
| Tool calls | **533** |
| Compactions | **2** |
| Files touched | **77** |
| Agent lines added | **~6,138** |
| Agent lines removed | **~306** |

### Tokens

| What | Value |
|---|---:|
| Context window | **500,000** |
| Context in use at Session 2 wrap | **~89,546** (~**18%**, after compaction) |
| Lifetime billed in/out tokens | **Not exposed** to the agent — check xAI / Grok Build usage dashboard |

`contextTokensUsed` is **window occupancy**, not the sum of every turn.

### Product API spend (art, cumulative)

| Item | Estimate |
|---|---:|
| Live Imagine images | **22** × ~$0.02 ≈ **~$0.44** |
| X posts recorded | **~16** |
| Peak night (if full window) | ~9–12 fires ≈ **~$0.18–0.48** Imagine |

---

## Docs

| Doc | |
|---|---|
| [`docs/BEELINK-INSTALL.md`](docs/BEELINK-INSTALL.md) | Beelink / Starlink install |
| [`docs/STYLE-SEEDS.md`](docs/STYLE-SEEDS.md) | Add / share style seeds |
| [`docs/CREATIVE-BRIEF.md`](docs/CREATIVE-BRIEF.md) | Series look |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Topology |
| [`docs/DEPLOY-STRIKELIST.md`](docs/DEPLOY-STRIKELIST.md) | Deploy checklist |
| [`docs/SESSION-2-PLAN.md`](docs/SESSION-2-PLAN.md) | Session 2 decisions |
| [`docs/STATS.md`](docs/STATS.md) | Whole-repo LOC + spend index |
| [`docs/STATS-SESSION-1.md`](docs/STATS-SESSION-1.md) | Session 1 tallies |
| [`docs/STATS-SESSION-2.md`](docs/STATS-SESSION-2.md) | Session 2 tallies |
| [`GROK.md`](GROK.md) | Agent rules |

---

## Layout

```text
backend/     FastAPI + pipeline + news stream + X publish
frontend/    Studio + Gallery control plane
worker/      one-shot CLI
docs/        install, styles, creative, stats
art/         generated assets (gitignored content)
scripts/     X OAuth pin finish helper
```
