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

# Lean free RSS (4 BBC feeds). TTL avoids re-download every generate.
RSS_INGEST_TTL_MINUTES=45
# X Recent Search is PAID — keep OFF. Publish still works.
X_SEARCH_ENABLED=false
X_SEARCH_TTL_MINUTES=120

# optional local text model on Beelink
EDGE_TEXT=xai
LEMONADE_URL=http://127.0.0.1:13305
LEMONADE_MODEL=Qwen3-4B-GGUF

# --- scheduler OFF — you trigger generate; optional auto-post after ---
SCHEDULE_ENABLED=false
AUTO_PUBLISH=true
# Optional if you re-enable scheduler later:
# SCHEDULE_INTERVAL_MINUTES=40
# SCHEDULE_MAX_RUNS_PER_DAY=5
# SCHEDULE_TIMEZONE=America/New_York

# --- X / @tunastarlink (OAuth 1.0a) ---
# post+media only by default; search is X_SEARCH_ENABLED (off).
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
SCHEDULE_ENABLED=false
AUTO_PUBLISH=true
EVENTS_SOURCE=stream
X_SEARCH_ENABLED=false
```

No background fires. Click **Generate** when you want a piece; with `AUTO_PUBLISH` it posts after success. No X search. **~$0.02–0.04 xAI per intentional generate** (Imagine dominates).

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

Three Grok Build sessions, model **grok-4.5**.  
Index: [`docs/STATS.md`](docs/STATS.md) · [S1](docs/STATS-SESSION-1.md) · [S2](docs/STATS-SESSION-2.md) · [S3](docs/STATS-SESSION-3.md).

### Lines of code (current repo)

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **2,974** |
| Frontend (`frontend/src`) | **1,147** |
| Style seeds + compose YAML | **135** |
| **Application code** | **~4,256** |
| Docs (`docs/`, README, GROK) | **1,409** |
| Makefile / Dockerfile / `.env.example` / samples | **129** |
| **All product files** | **~5,794** |

(Excludes `node_modules`, `.venv`, generated `art/`, lockfiles.) S2→S3 ≈ **+322** app / **~+464** product (cost gates + lean wire + stats).

### Combined session activity (S1–S3)

| Metric | Value |
|---|---:|
| Active engineering time | **~5.7 hours** (excludes idle) |
| User turns | **64** |
| Assistant messages | **273** |
| Tool calls | **618** |
| Compactions | **2** |
| Files touched (sum of snapshots) | **88** |
| Agent lines added | **~6,601** |
| Agent lines removed | **~421** |

### Tokens

| What | Value |
|---|---:|
| Context window | **500,000** |
| Context in use at Session 3 wrap | **~89,732** (~**18%**) |
| Lifetime billed in/out tokens | **Not exposed** — xAI / Grok Build dashboard |

`contextTokensUsed` is **window occupancy**, not the sum of every turn.

### Product API spend (art, cumulative)

| Item | Estimate |
|---|---:|
| Live Imagine images | **23** × ~$0.02 ≈ **~$0.46** |
| X posts recorded | **~17** |
| X Recent Search | **OFF** |
| Unattended schedule | **OFF** (manual generate) |

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
| [`docs/STATS-SESSION-3.md`](docs/STATS-SESSION-3.md) | Session 3 tallies (cost control) |
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
