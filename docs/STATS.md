# Planet Hack — build stats (whole repo)

Rolling tallies for **tuna-starlink-app**. Per-session write-ups:

| Session | File | When | Focus |
|---|---|---|---|
| **1** | [`STATS-SESSION-1.md`](STATS-SESSION-1.md) | 2026-07-21/22 | Greenfield: RSS → Imagine → gallery → X |
| **2** | [`STATS-SESSION-2.md`](STATS-SESSION-2.md) | 2026-07-22 | Lanes, X search, peak schedule, wire pack, Generative Stream |
| **3** | [`STATS-SESSION-3.md`](STATS-SESSION-3.md) | 2026-07-22 | Cost control: X search off, lean RSS, scheduler off |
| **4** | [`STATS-SESSION-4.md`](STATS-SESSION-4.md) | 2026-07-23 | Stream-render experiments → classic Imagine restore; Stream = X body |

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.5  

---

## Whole-repo lines of code (current)

Counted at Session 4 wrap (**2026-07-23**). Excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`.

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **3,291** |
| Frontend (`frontend/src` — ts/tsx/css) | **1,165** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **135** |
| **Application code subtotal** | **~4,591** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **1,524** |
| Makefile, Dockerfile, `.env.example`, samples | **129** |
| **All product files** | **~6,244** |

### Growth across sessions

| | S1 wrap | S2 wrap | S3 wrap | S4 wrap (now) |
|---|---:|---:|---:|---:|
| Application code | ~3,135 | ~3,934 | ~4,256 | **~4,591** |
| All product files | ~3,999 | ~5,330 | ~5,794 | **~6,244** |

| Δ | App | All product |
|---|---:|---:|
| S1 → S2 | +799 | +1,331 |
| S2 → S3 | +322 | ~+464 |
| S3 → S4 | **~+335** | **~+450** |

### By language (product tree, current)

| Ext | Lines |
|---|---:|
| `.py` | 3,291 |
| `.md` | 1,524 |
| `.tsx` | ~1,038 |
| `.ts` | ~154 |
| `.yaml` / `.yml` | 135 |
| other (Makefile, Dockerfile, env.example, …) | ~129 |

---

## Combined Grok session activity (S1–S4)

| Metric | Value |
|---|---:|
| **Active engineering time (S1–S4)** | **~7.3–7.5 h** (~2.65 + ~2.5 + ~0.5 + ~1.6) |
| User messages | **89** (64 + 25) |
| Assistant messages | **385** (273 + 112) |
| Tool calls | **806** (618 + 188) |
| Compactions | **2** |
| Files touched (agent, sum of snapshots) | **102** (88 + 14; overlap possible) |
| Agent lines added | **~7,396** |
| Agent lines removed | **~764** |
| Context window | **500,000** |
| Context in use at S4 wrap | **~219,794** (~**44%**) |

**Note:** Raw Grok wall-clock can include idle — report **active engineering time** only.

Session-level detail: Session 1–4 files above.

---

## Spend (product APIs, cumulative art)

| Item | Estimate |
|---|---:|
| Live gallery Imagine PNGs (`art/*/art.png`) | **19** × ~$0.02 ≈ **~$0.38** |
| Experiment / develop images (non-field) | **~17** × ~$0.02 ≈ **~$0.34** |
| X posts recorded on runs | **~4** with `x_post_id` this host snapshot |
| X Recent Search | **OFF** (`X_SEARCH_ENABLED=false`) |
| Unattended schedule | **OFF** (`SCHEDULE_ENABLED=false`) — manual generate only |
| xAI chat (director / stream expand) | Non-reasoning default; not metered in-repo |
| Grok Build agent tokens (invoice) | **Not exposed** — use xAI / Grok Build dashboard |

Practice: re-measure LOC + session signals at each session wrap; keep product API spend (Imagine count × unit price) in the same note.

---

## Product shape (current)

```
style → news lane
  → lean RSS (4 BBC feeds, 45m TTL)  [X search off]
  → single story (title + summary)
  → Grok art director (non-reasoning chat)
  → xAI Imagine 16:9
  → main: Generative Stream body (~fill 280, no hashtags)
  → no reply
```

**Ops:** `SCHEDULE_ENABLED=false` — click Generate when you want to spend.  
`AUTO_PUBLISH` optional after a successful generate. `X_SEARCH_ENABLED=false`.

---

*Regenerate LOC anytime:*

```bash
python3 .grok/skills/session-wrap/scripts/measure_loc.py
```
