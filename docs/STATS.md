# Planet Hack — build stats (whole repo)

Rolling tallies for **tuna-starlink-app**. Per-session write-ups:

| Session | File | When | Focus |
|---|---|---|---|
| **1** | [`STATS-SESSION-1.md`](STATS-SESSION-1.md) | 2026-07-21/22 | Greenfield: RSS → Imagine → gallery → X |
| **2** | [`STATS-SESSION-2.md`](STATS-SESSION-2.md) | 2026-07-22 | Lanes, X search, peak schedule, wire pack, Generative Stream |
| **3** | [`STATS-SESSION-3.md`](STATS-SESSION-3.md) | 2026-07-22 | Cost control: X search off, lean RSS, scheduler off |

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.5  

---

## Whole-repo lines of code (current)

Counted at Session 3 wrap (**2026-07-22**). Excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`.

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **2,974** |
| Frontend (`frontend/src` — ts/tsx/css) | **1,147** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **135** |
| **Application code subtotal** | **~4,256** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **1,409** |
| Makefile, Dockerfile, `.env.example`, samples | **129** |
| **All product files** | **~5,794** |

### Growth across sessions

| | Session 1 wrap | Session 2 wrap | Session 3 wrap (now) |
|---|---:|---:|---:|
| Application code | ~3,135 | ~3,934 | **~4,256** |
| All product files | ~3,999 | ~5,330 | **~5,794** |

| Δ | App | All product |
|---|---:|---:|
| S1 → S2 | +799 | +1,331 |
| S2 → S3 | **+322** | **~+464** |

### By language (product tree, current)

| Ext | Lines |
|---|---:|
| `.py` | 2,974 |
| `.md` | 1,409 |
| `.tsx` | 1,020 |
| `.ts` | 154 |
| `.yaml` / `.yml` | 135 |
| other (Makefile, Dockerfile, env.example, …) | ~129 |

---

## Combined Grok session activity (S1 + S2 + S3)

S1+S2 were one continuous conversation; S3 is a new session focused on cost.

| Metric | Value |
|---|---:|
| **Active engineering time (S1–S3)** | **~5.7 h** (~2.65 + ~2.5 + ~0.5) |
| User messages | **64** (60 + 4) |
| Assistant messages | **273** (249 + 24) |
| Tool calls | **618** (533 + 85) |
| Compactions | **2** |
| Files touched (agent, sum of snapshots) | **88** (77 + 11; overlap possible) |
| Agent lines added | **~6,601** |
| Agent lines removed | **~421** |
| Context window | **500,000** |
| Context in use at S3 wrap | **~89,732** (~18%) |

**Note:** Raw Grok wall-clock can include idle — report **active engineering time** only.

Session-level detail: Session 1 / 2 / 3 files above.

---

## Spend (product APIs, cumulative art)

| Item | Estimate |
|---|---:|
| Live Imagine images on disk | **23** × ~$0.02 ≈ **~$0.46** |
| Image payload total | **~9.7 MB** |
| X posts recorded on runs | **~17** |
| X Recent Search | **OFF** (`X_SEARCH_ENABLED=false`) — was the cost spike |
| Unattended schedule | **OFF** (`SCHEDULE_ENABLED=false`) — manual generate only |
| xAI chat (director / caption) | Non-reasoning default; not metered in-repo |
| Grok Build agent tokens (invoice) | **Not exposed** — use xAI / Grok Build dashboard |

Practice: re-measure LOC + session signals at each session wrap; keep product API spend (Imagine count × unit price) in the same note.

---

## Product shape (current)

```
style → news lane
  → lean RSS (4 BBC feeds, 45m TTL)  [X search off]
  → 2-headline wire pack (primary first)
  → Grok art director (non-reasoning chat)
  → xAI Imagine 16:9
  → main: mood caption + #PlanetHack #StyleCamel
  → reply: Generative Stream (~280, multi-headline)
```

**Ops:** `SCHEDULE_ENABLED=false` — click Generate when you want to spend.  
`AUTO_PUBLISH` optional after a successful generate. `X_SEARCH_ENABLED=false`.

---

*Regenerate LOC anytime:*

```bash
python3 .grok/skills/session-wrap/scripts/measure_loc.py
```
