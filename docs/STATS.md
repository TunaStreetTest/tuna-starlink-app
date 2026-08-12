# Planet Hack — build stats (whole repo)

Rolling tallies for **tuna-starlink-app**. Per-session write-ups:

| Session | File | When | Focus |
|---|---|---|---|
| **1** | [`STATS-SESSION-1.md`](STATS-SESSION-1.md) | 2026-07-21/22 | Greenfield: RSS → Imagine → gallery → X |
| **2** | [`STATS-SESSION-2.md`](STATS-SESSION-2.md) | 2026-07-22 | Lanes, X search, peak schedule, wire pack, Generative Stream |
| **3** | [`STATS-SESSION-3.md`](STATS-SESSION-3.md) | 2026-07-22 | Cost control: X search off, lean RSS, scheduler off |
| **4** | [`STATS-SESSION-4.md`](STATS-SESSION-4.md) | 2026-07-23 | Stream-render experiments → classic Imagine; Stream = X body |
| **5** | [`STATS-SESSION-5.md`](STATS-SESSION-5.md) | 2026-07-24/25 | Cool-tech wire + matrix prompts + systemd service |
| **6** | [`STATS-SESSION-6.md`](STATS-SESSION-6.md) | 2026-07-26 | Art direction polish + **Data Space**; classic Data Tunnel |
| **7** | [`STATS-SESSION-7.md`](STATS-SESSION-7.md) | 2026-07-28 | Studio merge · neon spectrum restore · lean newest-first wire |
| **8** | [`STATS-SESSION-8.md`](STATS-SESSION-8.md) | 2026-07-29 | Rootkit cityscape · kill lightning motif · Grok 4.5 art director |
| **9** | [`STATS-SESSION-9.md`](STATS-SESSION-9.md) | 2026-07-29 | Source-only captions · primary X brands · no news invent |
| **10** | [`STATS-SESSION-10.md`](STATS-SESSION-10.md) | 2026-07-30 | Dense Rootkit City · durable never-reuse news ledger |
| **11** | [`STATS-SESSION-11.md`](STATS-SESSION-11.md) | 2026-08-12 | Magical franchise stills · event wire · caption holes |
| **12** | [`STATS-SESSION-12.md`](STATS-SESSION-12.md) | 2026-08-12 | Studio native fullscreen + stack walk |

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.6 (S11–S12); earlier sessions grok-4.5

---

## Whole-repo lines of code (current)

Counted at Session 12 wrap (**2026-08-12**). Excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`.

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **4,560** |
| Frontend (`frontend/src` — ts/tsx/css) | **1,122** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **169** |
| **Application code subtotal** | **~5,851** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **2,469** |
| Makefile, Dockerfile, `.env.example`, samples | **133** |
| **All product files** | **~8,453** |

### Growth across sessions

| | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 | S11 | S12 (now) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Application code | ~3,135 | ~3,934 | ~4,256 | ~4,591 | ~4,687 | ~4,781 | ~4,751 | ~4,901 | ~4,904 | ~5,350 | ~5,634 | **~5,851** |
| All product files | ~3,999 | ~5,330 | ~5,794 | ~6,244 | ~6,521 | ~6,610 | ~6,802 | ~7,066 | ~7,180 | ~7,727 | ~8,127 | **~8,453** |

| Δ | App | All product |
|---|---:|---:|
| S1 → S2 | +799 | +1,331 |
| S2 → S3 | +322 | ~+464 |
| S3 → S4 | ~+335 | ~+450 |
| S4 → S5 | ~+96 | ~+277 |
| S5 → S6 | ~+94 | ~+89 |
| S6 → S7 | ~−30 | ~+192 |
| S7 → S8 | ~+150 | ~+264 |
| S8 → S9 | ~+3 | ~+114 |
| S9 → S10 | ~+446 | ~+547 |
| S10 → S11 | ~+284 | ~+400 |
| S11 → S12 | **~+217** | **~+326** |

*(S12: Studio gallery native fullscreen + left/right stack walk.)*

### By language (product tree, current)

| Ext | Lines |
|---|---:|
| `.py` | 4,560 |
| `.md` | 2,469 |
| `.tsx` / `.ts` / `.css` | 1,122 |
| `.yaml` / `.yml` | 169 |
| other | ~133 |

---

## Combined Grok session activity (S1–S12)

| Metric | Value |
|---|---:|
| **Active engineering time (S1–S12)** | **~11.3–13.0 h** (~11.0–12.6 + ~0.25–0.4) |
| User messages | **~126–127** (123–124 + ~3) |
| Assistant messages | **~649** (620 + ~29) |
| Tool calls | **~1,427** (1,368 + ~59) |
| Compactions | **2** |
| Files touched (agent, sum of snapshots) | **~173** (171 + 2; overlap possible) |
| Agent lines added | **~10,647** |
| Agent lines removed | **~1,865** |
| Context window | **500,000** |
| Context in use at S12 wrap | **~170,918** (~**34%**) |

**Note:** Report **active engineering time** only — wall clock includes idle.

---

## Spend (product APIs, cumulative art)

| Item | Estimate |
|---|---:|
| Live gallery Imagine PNGs (`art/*/art.png`) | **88** (23 quality ~$0.05 + rest ~$0.02) ≈ **~$2.05–2.45** |
| Experiment / develop images (earlier) | **~17** × ~$0.02 ≈ **~$0.34** |
| X posts recorded in meta | **~53–57** |
| X Recent Search | **Primary-only when enabled** (official brands; TTL 120m). Event + fluff gated. Used ledger blocks re-picks. |
| Unattended schedule | **OFF** (systemd keeps API up; generate manual) |
| Wire | Lean cool-tech RSS + optional primary X; **visualizable events only**; durable never-reuse ledger; 72h max age |
| Styles | `data-space`, `planet-core`, `data-tunnel`, `signal-cathedral`, `rootkit-city` |
| Art director | **Grok 4.5** (`XAI_ART_MODEL`) → 2–5 sentence SHOT; **caption is source-only** (handles → names) |
| Imagine | `grok-imagine-image-quality` @ **1K** (skip 2K); SHOT + short lock; craft > resolution |
| Studio | Tile modal → native **Fullscreen** (monitor) → ← → walk image stack |
| Grok Build agent tokens | **Not exposed** — dashboard |

---

## Product shape (current)

```
Studio (single page)
  → Generate (style pick) + gallery tiles → modal → Post to X
  → tile image / Fullscreen → native monitor fullscreen; ← → walk stack
  → wire: primary X brands (when search on) else cool-tech RSS
  → single story — visualizable event only (launch / chip / model; no games/IR)
  → caption = source text only (no invent); @handles → names; full clip to 280
  → used ledger: posted/generated clips never re-picked
  → Grok 4.5 art director (SHOT: 2–5 sentences, one poetic plate; no people)
  → Imagine prompt = SHOT + short lock (no cube-farm recipe stack)
  → xAI Imagine 16:9 quality @ 1K
  → X main: source-only stream body, no hashtags, no reply
```

**Trust bar:** X caption never invents facts past the wire.  
**Craft bar:** one impossible architecture + photoreal materials + dual warm/cool light.  
**Rootkit City:** one luminous digital-city hero inside the computer (glass-silicon keep / canyon); green = building lights or vertical code-rain — never path/bolt lightning; never a packed server-rack farm.  
**Wire reuse:** `art/.news_used.json` — ids + title fingerprints; seed from gallery; mark on tap / complete / post.  
**Data Space:** deep space; few satellites max.  
**Data Tunnel:** busy packet tunnel.  
**Runtime:** `systemctl --user` or Docker; schedule **OFF** by default.

---

*Regenerate LOC anytime:*

```bash
python3 .grok/skills/session-wrap/scripts/measure_loc.py
```
