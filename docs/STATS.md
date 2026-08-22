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
| **13** | [`STATS-SESSION-13.md`](STATS-SESSION-13.md) | 2026-08-22 | Tuna Starlink long posts · heaven/Tron kill · Imagine API |

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.6 (S11–S13); earlier sessions grok-4.5

---

## Whole-repo lines of code (current)

Counted at Session 13 wrap (**2026-08-22**). Excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`.

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **4,778** |
| Frontend (`frontend/src` — ts/tsx/css) | **1,122** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **168** |
| **Application code subtotal** | **~6,068** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **2,587** |
| Makefile, Dockerfile, `.env.example`, samples | **133** |
| **All product files** | **~8,788** |

### Growth across sessions

| | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 | S11 | S12 | S13 (now) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Application code | ~3,135 | ~3,934 | ~4,256 | ~4,591 | ~4,687 | ~4,781 | ~4,751 | ~4,901 | ~4,904 | ~5,350 | ~5,634 | ~5,851 | **~6,068** |
| All product files | ~3,999 | ~5,330 | ~5,794 | ~6,244 | ~6,521 | ~6,610 | ~6,802 | ~7,066 | ~7,180 | ~7,727 | ~8,127 | ~8,453 | **~8,788** |

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
| S11 → S12 | ~+217 | ~+326 |
| S12 → S13 | **~+217** | **~+335** |

*(S13: Tuna Starlink caption + fluff gates + Imagine `size` fix + neon-on-materials lock.)*

### By language (product tree, current)

| Ext | Lines |
|---|---:|
| `.py` | 4,778 |
| `.md` | 2,587 |
| `.tsx` / `.ts` / `.css` | 1,122 |
| `.yaml` / `.yml` | 168 |
| other | ~133 |

---

## Combined Grok session activity (S1–S13)

| Metric | Value |
|---|---:|
| **Active engineering time (S1–S13)** | **~12.5–14.6 h** (~11.3–13.0 + ~1.2–1.6) |
| User messages | **~133–134** (126–127 + 7) |
| Assistant messages | **~736** (649 + 87) |
| Tool calls | **~1,661** (1,427 + 234) |
| Compactions | **2** |
| Files touched (agent, sum of snapshots) | **~191** (173 + 18; overlap possible) |
| Agent lines added | **~11,492** (10,647 + 845) |
| Agent lines removed | **~2,048** (1,865 + 183) |
| Context window | **500,000** |
| Context in use at S13 wrap | **~207,360** (~**41%**) |

**Note:** Report **active engineering time** only — wall clock includes idle.

---

## Spend (product APIs, cumulative art)

| Item | Estimate |
|---|---:|
| Live gallery Imagine PNGs (`art/*/art.png`) | **105** (40 quality ~$0.05 + rest ~$0.02) ≈ **~$2.85–3.30** |
| Experiment / develop images (earlier) | **~17** × ~$0.02 ≈ **~$0.34** |
| X posts recorded in meta | **59** |
| X Recent Search | **Primary-only when enabled** (official brands; TTL 120m). Event + fluff gated (giveaway / air-show / risk-report too). Used ledger blocks re-picks. |
| Unattended schedule | **OFF** (systemd keeps API up; generate manual) |
| Wire | Lean cool-tech RSS + optional primary X; **visualizable events only**; durable never-reuse ledger; 72h max age |
| Styles | `data-space`, `planet-core`, `data-tunnel`, `signal-cathedral`, `rootkit-city` |
| Art director | **Grok 4.5** (`XAI_ART_MODEL`) → 2–5 sentence SHOT; neon as light on materials |
| Caption | **Tuna Starlink** long body (facts from wire only); `stream_slug` is the ledger line |
| Imagine | `grok-imagine-image-quality` @ **1K** 16:9 (`aspect_ratio` + `resolution`; do **not** send `size`) |
| Studio | Tile modal → native **Fullscreen** (monitor) → ← → walk image stack; full X post preview |
| Grok Build agent tokens | **Not exposed** — dashboard |

---

## Product shape (current)

```
Studio (single page)
  → Generate (style pick) + gallery tiles → modal → Post to X
  → tile image / Fullscreen → native monitor fullscreen; ← → walk stack
  → wire: primary X brands (when search on) else cool-tech RSS
  → single story — visualizable event only (launch / chip / model; no games/IR/giveaway)
  → caption = Tuna Starlink voice, 500–1200 chars; facts from wire only
  → stream_slug = source-only ledger (never-reuse)
  → used ledger: posted/generated clips never re-picked
  → Grok 4.5 art director (SHOT: 2–5 sentences; neon as light on materials)
  → Imagine prompt = SHOT + short lock (no Tron outlines, no HUD globe, no heaven)
  → xAI Imagine 16:9 quality @ 1K (aspect_ratio + resolution)
  → X main: Tuna Starlink caption on the image, no hashtags, no reply
```

**Trust bar:** X caption never invents facts past the wire. Identity (studio runs on Starlink) is allowed; extra news is not.  
**Craft bar:** premium CGI, neon as illumination on real materials — not Tron stickers, not church god-rays.  
**Rootkit City:** one luminous digital-city hero inside the computer; green = building lights or vertical code-rain.  
**Data Space:** cinematic craft + real planet + neon rings (July 28 composition).  
**Data Tunnel:** packed packet conduit with physical ribs (July 24), not a vector preset.  
**Runtime:** `systemctl --user` or Docker; schedule **OFF** by default.

---

*Regenerate LOC anytime:*

```bash
python3 .grok/skills/session-wrap/scripts/measure_loc.py
```
