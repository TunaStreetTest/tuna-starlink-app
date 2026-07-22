# Deploy strike list — TunaStarLink / Planet Hack

**Full Beelink steps:** [`docs/BEELINK-INSTALL.md`](BEELINK-INSTALL.md).

---

## A. Local laptop / gaming PC WSL

- [x] Repo at `~/tuna-starlink-app`
- [ ] `make dry-run` succeeds
- [ ] `make backend` + `make frontend` — Studio UI loads
- [ ] One **real** generation (`DRY_RUN=false` + `XAI_API_KEY`) produces a PNG worth looking at
- [ ] X tokens for **@tunastarlink** in `backend/.env.local`
- [ ] Optional: try all four styles once

---

## B. Beelink `TunaStarlink` (primary home)

### Prerequisites

- [x] Windows host on Starlink
- [x] Tailscale (optional for remote UI)
- [x] Lemonade optional (text only)
- [ ] Docker Desktop **or** Python 3.12 + Node 20

### Install

- [ ] Clone or copy `tuna-starlink-app` onto the Beelink
- [ ] Create art directory (e.g. `D:\TunaStarLink\art` or repo `./art`)
- [ ] Create `.env` next to `docker-compose.yml` (see README full env — XAI + all four X OAuth fields)

```env
XAI_API_KEY=...
DRY_RUN=false
ART_STORAGE_PATH=/art
DEFAULT_STYLE=data-tunnel
EVENTS_SOURCE=stream
SCHEDULE_ENABLED=true
SCHEDULE_CRON=0 * * * *
AUTO_PUBLISH=true
EDGE_TEXT=xai
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
X_ACCOUNT_HANDLE=@tunastarlink
```

- [ ] `docker compose up --build -d`  **or** native backend + static frontend
- [ ] Open `http://127.0.0.1:8091` (compose) or `:8010`
- [ ] Generate one piece; confirm X thread (main + news reply)
- [ ] Leave running for schedule / overnight

### Optional later

- [ ] Tailscale expose UI to the array
- [ ] `EDGE_TEXT=lemonade` for local text (Qwen3 needs room for reasoning / `/no_think`)

---

## C. Quality gate for automation

- [x] Real Imagine pieces postable on @tunastarlink
- [x] Style rotation (random hourly)
- [x] News stream taps fresh headlines
- [ ] Beelink install day
