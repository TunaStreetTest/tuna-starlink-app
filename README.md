# TunaStarLink App — Planet Hack

Cool tech wire (**SpaceX / Tesla / xAI / NVIDIA / AI**) → **newest story first** → **Grok art director** → **xAI Imagine** (neon matrix CGI) → Studio gallery → **@tunastarlink** on X.

Series look: hacker-movie **3D digital cyberspace / hacking the planet**.  
Home host: **Beelink SER9 (`TunaStarlink`)** on Starlink (also runs fine on a laptop).

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app

---

## Product

Each run:

1. **Ingest** lean cool-tech RSS (**3 feeds**, last ~3 days) into `art/.news_stream.json` — drop stories older than **72h**; block soft “photo of the day” features
2. **Single story** — prefer **official X brand posts** (SpaceX / Tesla / NVIDIA / xAI …) when `X_SEARCH_ENABLED`; else newest RSS (publish-time rank)
3. **Art director** (Grok) metaphors that story into a visual brief — **full neon spectrum**
4. **Imagine** (`grok-imagine-image-quality`, ~$0.05 1K / ~$0.07 2K, landscape 16:9)
5. Save `art/<run_id>/art.png` + `meta.json`
6. **X post** from Studio tile modal (or `AUTO_PUBLISH`) — image + **source-only** Generative Stream body (wire text clipped to ~280, **no LLM invent**, **no hashtags**, no reply)

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
XAI_IMAGE_MODEL=grok-imagine-image-quality
XAI_IMAGE_RESOLUTION=1k
XAI_IMAGE_SIZE=1792x1024
XAI_IMAGE_ASPECT_RATIO=16:9

DEFAULT_STYLE=data-tunnel
EVENTS_SOURCE=stream

# Lean free RSS. TTL avoids re-download every generate.
RSS_INGEST_TTL_MINUTES=20
# X Recent Search is PAID. When ON: prefer official brand posts (primary-only).
# Publish still works with search OFF (RSS caption = source text only).
X_SEARCH_ENABLED=false
X_SEARCH_PRIMARY_ONLY=true
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

**Studio** → gallery tile → modal → **Post to X**, or enable `AUTO_PUBLISH=true` after generate.

---

## Overnight

```env
SCHEDULE_ENABLED=false
AUTO_PUBLISH=true
EVENTS_SOURCE=stream
X_SEARCH_ENABLED=false
```

No background fires. Click **Generate** when you want a piece; with `AUTO_PUBLISH` it posts after success. No X search. **~$0.05–0.07 xAI per intentional generate** (quality Imagine dominates; set `XAI_IMAGE_MODEL=grok-imagine-image` for ~$0.02 cheap runs).

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

Nine Grok Build sessions, model **grok-4.5**.  
Index: [`docs/STATS.md`](docs/STATS.md) · [S1](docs/STATS-SESSION-1.md) · [S2](docs/STATS-SESSION-2.md) · [S3](docs/STATS-SESSION-3.md) · [S4](docs/STATS-SESSION-4.md) · [S5](docs/STATS-SESSION-5.md) · [S6](docs/STATS-SESSION-6.md) · [S7](docs/STATS-SESSION-7.md) · [S8](docs/STATS-SESSION-8.md) · [S9](docs/STATS-SESSION-9.md).

### Lines of code (current repo)

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **3,829** |
| Frontend (`frontend/src`) | **905** |
| Style seeds + compose YAML | **170** |
| **Application code** | **~4,904** |
| Docs (`docs/`, README, GROK) | **2,143** |
| Makefile / Dockerfile / `.env.example` / samples | **133** |
| **All product files** | **~7,180** |

(Excludes `node_modules`, `.venv`, generated `art/`, lockfiles.) S8→S9 ≈ **+3** app / **~+114** product (source-only captions + primary X wire).

### Combined session activity (S1–S9)

| Metric | Value |
|---|---:|
| Active engineering time | **~10.3–11.6 hours** (excludes idle) |
| User turns | **~118–119** |
| Assistant messages | **~558** |
| Tool calls | **~1,188** |
| Compactions | **2** |
| Files touched (sum of snapshots) | **~151** |
| Agent lines added | **~9,258** |
| Agent lines removed | **~1,586** |

### Tokens

| What | Value |
|---|---:|
| Context window | **500,000** |
| Context in use at Session 9 wrap | **~87,496** (~**17%**) |
| Lifetime billed in/out tokens | **Not exposed** — xAI / Grok Build dashboard |

`contextTokensUsed` is **window occupancy**, not the sum of every turn.

### Product API spend (art, cumulative)

| Item | Estimate |
|---|---:|
| Live gallery Imagine images | **70** (mix ~$0.02 + quality ~$0.05) ≈ **~$1.55–1.75** |
| Experiment images (non-field) | **~17** × ~$0.02 ≈ **~$0.34** |
| X Recent Search | **Primary-only when enabled** (official brands) |
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
| [`docs/STATS-SESSION-7.md`](docs/STATS-SESSION-7.md) | Session 7 tallies (Studio merge + neon + wire) |
| [`docs/STATS-SESSION-8.md`](docs/STATS-SESSION-8.md) | Session 8 tallies (rootkit craft + Grok 4.5 art director) |
| [`docs/STATS-SESSION-9.md`](docs/STATS-SESSION-9.md) | Session 9 tallies (source-only captions + primary X) |
| [`GROK.md`](GROK.md) | Agent rules |

---

## Layout

```text
backend/     FastAPI + pipeline + cool-tech stream + X publish
frontend/    Studio control plane (generate + gallery + Post to X)
worker/      one-shot CLI
deploy/      systemd unit (tuna-starlink.service)
scripts/     install-persist.sh (user service)
docs/        install, styles, creative, stats
art/         generated assets (gitignored content)
scripts/     X OAuth pin finish helper
```
