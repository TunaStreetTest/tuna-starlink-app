# Read this first (TunaStarLink / Picasso Starlink)

This is a **new, lean app** — not a clone of `cso-operator-app`.

## Scope (hard)

- **In:** FastAPI + React control plane, xAI chat (events) + Imagine (images), local art gallery, style presets, optional scheduler, optional Lemonade for *text only*.
- **Out for now:** Kafka, EFM, NiFi, Minikube lab pod, full CSO stack on Beelink, local Stable Diffusion, auto-post to X until Steven asks.

## Live infra safety

- **Never** modify `/home/tunas/cso-operator-app` deploys, PVCs, env, or NiFi Streamers flows.
- This app does not share `clips-storage` or streamers topics.
- Credentials stay in `.env` / env vars — never commit secrets.

## Hosting home

Primary host is the **Beelink TunaStarlink** (Windows, Starlink). Optimize for:
- One image download per run (cloud Imagine)
- Small install footprint
- Manual X post is fine (`@tunastarlink`) — download PNG + copy caption

## Key paths

| Path | Role |
|---|---|
| `backend/services/pipeline.py` | Generate orchestration |
| `backend/prompts/styles.yaml` | Art style presets |
| `art/<run_id>/` | PNG + meta.json gallery |
| `docs/DEPLOY-STRIKELIST.md` | When (not if) we install on Beelink |
| `DesktopShare/tuna-starlink-app.md` | Golden narrative doc |

## Dev defaults

```bash
make dry-run          # no API spend
make backend          # :8001
make frontend         # :5174
```

Real image: set `XAI_API_KEY` and `DRY_RUN=false` in `backend/.env.local`.
