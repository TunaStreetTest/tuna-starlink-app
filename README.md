# TunaStarLink App — Planet Hack

Cool tech wire (**SpaceX / GPU / AI models**) → **stream tap** → **Grok art director** → **xAI Imagine** (matrix CGI) → gallery → **@tunastarlink** on X.

Series look: hacker-movie **3D digital cyberspace / hacking the planet**.  
Home host: **Beelink SER9 (`TunaStarlink`)** on Starlink (also runs fine on a laptop).

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app

---

## Product

Each run:

1. **Ingest** cool-tech RSS (SpaceX, NVIDIA/GPU, AI model releases) into `art/.news_stream.json`
2. **Single story** from the style’s lane (`space` / `ai` / `gpu`) — full title + summary
3. **Art director** (Grok) metaphors that story into a visual brief
4. **Imagine** (`grok-imagine-image`, ~$0.02, landscape 16:9)
5. Save `art/<run_id>/art.png` + `meta.json`
6. **X post** (manual or `AUTO_PUBLISH`) — image + **Generative Stream** body (one story, fill ~280, **no hashtags**, no reply)

Downloads: `planethack_<run_id>.png`.

### Styles

| id | Lane | Shot |
|---|---|---|
| `data-space` | space | Deep space — planet(s), star, SpaceX-inspired craft (varies) |
| `planet-core` | space | Planetary mainframe / orbital compute |
| `data-tunnel` | ai | Speed data tunnel (classic vanishing-point) |
| `signal-cathedral` | space | Starlink / RF signal cathedral |
| `rootkit-city` | gpu | GPU die / datacenter circuit city |

Studio dropdown for manual runs (schedule **off** by default).  
Share new styles: [`docs/STYLE-SEEDS.md`](docs/STYLE-SEEDS.md).

---

## Quick start

```bash
cd ~/tuna-starlink-app
cp backend/.env.example backend/.env.local
# fill keys — see .env section below

make backend     # http://127.0.0.1:8010  (dev only — dies with the shell)
make frontend    # http://127.0.0.1:5174  (proxies /api → :8010)
```

### Run as a service (survives Grok / logout)

On Beelink WSL (recommended):

```bash
cd ~/tuna-starlink-app
make install-backend
# optional UI: cd frontend && npm install && npm run build && cp -r dist/* ../backend/static/
bash scripts/install-persist.sh
# http://127.0.0.1:8010
systemctl --user status tuna-starlink
```

Details: [`docs/BEELINK-INSTALL.md`](docs/BEELINK-INSTALL.md) §4C.  
Docker alternative: `docker compose up --build -d` → **http://127.0.0.1:8091** (`restart: unless-stopped`).

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
| Main | Image + **Generative Stream** — one story, fill ~280 chars, **no hashtags** |
| Reply | none |

Stored on each run: `x_url`, `x_post_id`, `stream_slug`, `events_source` in `meta.json`.

**Gallery** tab → tile → modal → **Post to X**, or enable `AUTO_PUBLISH=true` after generate.

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
| POST | `/api/publish/x` | `{ "run_id": "…" }` — image + Generative Stream body |

```bash
DRY_RUN=1 ART_STORAGE_PATH=./art python worker/run_once.py --style data-tunnel
```

---

## Build stats (whole repo)

Six Grok Build sessions, model **grok-4.5**.  
Index: [`docs/STATS.md`](docs/STATS.md) · [S1](docs/STATS-SESSION-1.md) · [S2](docs/STATS-SESSION-2.md) · [S3](docs/STATS-SESSION-3.md) · [S4](docs/STATS-SESSION-4.md) · [S5](docs/STATS-SESSION-5.md) · [S6](docs/STATS-SESSION-6.md).

### Lines of code (current repo)

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **3,446** |
| Frontend (`frontend/src`) | **1,165** |
| Style seeds + compose YAML | **170** |
| **Application code** | **~4,781** |
| Docs (`docs/`, README, GROK) | **1,700** |
| Makefile / Dockerfile / `.env.example` / samples | **129** |
| **All product files** | **~6,610** |

(Excludes `node_modules`, `.venv`, generated `art/`, lockfiles.) S5→S6 ≈ **+94** app / **~+89** product (Data Space + art locks).

### Combined session activity (S1–S6)

| Metric | Value |
|---|---:|
| Active engineering time | **~8.6–9.0 hours** (excludes idle) |
| User turns | **107** |
| Assistant messages | **453** |
| Tool calls | **920** |
| Compactions | **2** |
| Files touched (sum of snapshots) | **122** |
| Agent lines added | **~8,371** |
| Agent lines removed | **~1,140** |

### Tokens

| What | Value |
|---|---:|
| Context window | **500,000** |
| Context in use at Session 6 wrap | **~308,787** (~**62%**) |
| Lifetime billed in/out tokens | **Not exposed** — xAI / Grok Build dashboard |

`contextTokensUsed` is **window occupancy**, not the sum of every turn.

### Product API spend (art, cumulative)

| Item | Estimate |
|---|---:|
| Live gallery Imagine images | **44** × ~$0.02 ≈ **~$0.88** |
| Experiment images (non-field) | **~17** × ~$0.02 ≈ **~$0.34** |
| X Recent Search | **OFF** |
| Unattended schedule | **OFF** (service keeps API up; generate is manual) |

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
| [`docs/STATS-SESSION-4.md`](docs/STATS-SESSION-4.md) | Session 4 tallies (experiments + restore) |
| [`docs/STATS-SESSION-5.md`](docs/STATS-SESSION-5.md) | Session 5 tallies (cool-tech wire + service) |
| [`docs/STATS-SESSION-6.md`](docs/STATS-SESSION-6.md) | Session 6 tallies (Data Space + art polish) |
| [`GROK.md`](GROK.md) | Agent rules |

---

## Layout

```text
backend/     FastAPI + pipeline + cool-tech stream + X publish
frontend/    Studio + Gallery control plane
worker/      one-shot CLI
deploy/      systemd unit (tuna-starlink.service)
scripts/     install-persist.sh (user service)
docs/        install, styles, creative, stats
art/         generated assets (gitignored content)
scripts/     X OAuth pin finish helper
```
