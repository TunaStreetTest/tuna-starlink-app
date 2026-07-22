# Deploy strike list — TunaStarLink / Planet Hack

**Full Beelink steps:** see **`docs/BEELINK-INSTALL.md`** (ship this file with the repo dump).

No Kafka / EFM / NiFi / Minikube required on the Beelink for v1.

---

## A. Local laptop / gaming PC WSL (dev only — safe)

- [x] Repo at `~/tuna-starlink-app`
- [ ] `make dry-run` succeeds
- [ ] `make backend` + `make frontend` — Studio UI loads
- [ ] One **real** generation (`DRY_RUN=false` + `XAI_API_KEY`) produces a PNG worth looking at
- [ ] Optional: try all four styles once
- [ ] **Do not** deploy a pod next to `cso-operator-app` until deliberately approved (not needed for Beelink path)

---

## B. Beelink `TunaStarlink` (primary home)

### Prerequisites already on the box (from array work)

- [x] Windows host on Starlink
- [x] Tailscale (optional for remote UI; not required for local Picasso)
- [x] Lemonade optional (text only — not required for image path)
- [ ] Docker Desktop **or** Python 3.12 + Node 20

### Install app

- [ ] Copy or clone `tuna-starlink-app` onto the Beelink (USB / git / Tailscale share)
- [ ] Create art directory (e.g. `D:\TunaStarLink\art` or repo `./art`)
- [ ] Create `.env` next to `docker-compose.yml`:

```env
XAI_API_KEY=...
DRY_RUN=false
ART_STORAGE_PATH=/art
DEFAULT_STYLE=data-tunnel
SCHEDULE_ENABLED=true
SCHEDULE_CRON=0 * * * *
AUTO_PUBLISH=true
EDGE_TEXT=xai
# X tokens for @tunastarlink
```

- [ ] `docker compose up --build -d`  **or** native `make backend` / serve static build
- [ ] Open `http://127.0.0.1:8091` (compose) or frontend dev URL
- [ ] Generate one piece; confirm X thread (main + multi-part comments)
- [ ] Leave running for schedule / Starlink overnight

### Optional later

- [ ] Tailscale expose UI to array
- [ ] `EDGE_TEXT=lemonade` to save chat credits (Qwen3 needs room for reasoning / `/no_think`)
- [ ] Firewall / Tailscale expose UI to array machines
- [ ] Hybrid: emit metadata to gaming-PC Kafka (`picasso.*`) for CSO demos — **not required**

### Explicit non-goals on Beelink for this app

- [ ] ~~Full CFM/CSM/CSA Minikube~~
- [ ] ~~Local Stable Diffusion~~
- [ ] ~~Sharing streamers PVC / cso-operator-app env~~
- [ ] ~~NiFi process groups for Picasso~~

---

## C. Gaming PC cluster (optional lab — skip by default)

Only if you want the UI as a pod next to CSO for demos. **Separate names only.**

- [ ] Build image `tuna-starlink-app:latest` into minikube docker
- [ ] New resources only: `deploy/tuna-starlink-app`, `svc` port **8091**, own PVC for art
- [ ] `kubectl set env` on **that** deploy only for `XAI_API_KEY`
- [ ] Confirm `cso-operator-app` still Running, unchanged
- [ ] No shared `clips-storage`

---

## D. Quality gate before automation

- [ ] At least 3 real Imagine pieces you would actually post
- [ ] Style preset locked (or rotation decided)
- [ ] Caption tone OK for @tunastarlink brand
- [ ] Then consider schedule / auto-post

---

## Related docs

- `DesktopShare/xai-image-gen.md` — original World Picasso sketch
- `DesktopShare/beelink-starlink-efm-ai.md` — Beelink hardware / Lemonade / Tailscale facts
- `DesktopShare/tuna-starlink-app.md` — golden narrative for this project
