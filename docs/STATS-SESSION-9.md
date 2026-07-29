# Planet Hack — Session 9 build stats

**Dates:** 2026-07-29  
**Model:** grok-4.5  
**Phase:** Trust fix — source-only X captions · prefer primary brand posts · kill photo-of-day soft wire

Whole-repo totals: [`STATS.md`](STATS.md). Prior: [`STATS-SESSION-8.md`](STATS-SESSION-8.md).

**Session id:** `019faf2b-43c0-7cb0-828c-2102eb6cb043` (*Run ID News Source Dispute*).

---

## Goals / outcomes

| Goal | Outcome |
|---|---|
| Run `20260729_165153` caption was fabricated | **Root cause:** RSS headline only + Grok `craft_stream_slug` expanded short wire into invented “still in orbit / telemetry / no reentry” facts. Real Space.com story was **splashdown / floating in ocean**. |
| (1) Never invent caption facts | **Removed LLM expansion** from Generative Stream. Caption = cleaned source text only, clipped to 280. |
| (4) Prefer primary X / SpaceX over secondary RSS | Cool-tech lanes query **official accounts** first; when X search on, **always consult** and **outrank** Google News rewrites; `X_SEARCH_PRIMARY_ONLY` (one cheap query). |
| Soft “photo of the day” wire | **Blocked** at RSS ingest + pack; purged bad item from stream cache. |
| Trust | Humans treat the X body as news — no budget-filling fan-fiction. |

---

## Session activity (this session signals)

| Metric | Value |
|---|---:|
| User messages | **~3** (signals 2 + wrap) |
| Assistant messages | **~30+** (signals 27 pre-wrap) |
| Tool calls | **~60+** (signals 58 pre-wrap) |
| Files touched (agent) | **4** (+ stats docs at wrap) |
| Agent lines added | **~209** (+ docs) |
| Agent lines removed | **~138** |
| Compactions | **0** |
| Git commits (signal, pre-wrap) | **0** |
| Wall duration (s) | **~584+** (~10 m open pre-wrap) |
| **Active engineering time (S9)** | **~0.5–0.75 h** |

**Active time only** — wall clock includes short pause (`longPausesCount`: 1).

**Tools used:** `list_dir`, `grep`, `read_file`, `run_terminal_command`, `web_search`, `web_fetch`, `todo_write`, `search_replace`, `write`.

**Primary model:** grok-4.5.

---

## Tokens

| What | Value |
|---|---:|
| Context window | **500,000** |
| Context in use at wrap | **~87,496** (~**17%**) |
| Lifetime billed in/out | **Not exposed** — dashboard |

---

## Repo LOC growth (S8 wrap → S9 wrap)

| Area | Session 8 wrap | Session 9 wrap | **Δ** |
|---|---:|---:|---:|
| Python | 3,826 | **3,829** | **+3** |
| Frontend | 905 | **905** | **0** |
| YAML | 170 | **170** | **0** |
| **Application code** | ~4,901 | **~4,904** | **~+3** |
| Docs | 2,033 | **2,143** | **+110** |
| All product | ~7,066 | **~7,180** | **~+114** |

*(Product fix was mostly rewrite: caption path deleted ~100 lines of expand logic; X search rebalanced toward primary accounts.)*

---

## Spend (product APIs)

| Item | Estimate |
|---|---:|
| Live gallery Imagine PNGs | **70** (was 69) |
| Δ this session | **~+1** image (prior run already posted; no new Imagine in this fix session) |
| X posts recorded (meta) | **~40** |
| X Recent Search | **ON** in local `.env` for primary-only brand queries (TTL 120m); config default remains opt-in |
| Schedule | **OFF** (manual generate) |

---

## Product shipped (Session 9 checklist)

- [x] `craft_stream_slug` source-only — **no LLM invent**  
- [x] Soft “photo of the day” blocked from RSS + pack  
- [x] Cool-tech X lanes: SpaceX / Tesla / NVIDIA / xAI / OpenAI primary accounts  
- [x] When search enabled: always fetch X; primary ranks above RSS  
- [x] `X_SEARCH_PRIMARY_ONLY` setting  
- [x] Stream cache: purge bad soft item  
- [x] Backend restarted with fix  
- [x] Stats + ship  

---

## Commits

| SHA | Note |
|---|---|
| *(wrap)* | Session 9: source-only captions + primary X preference |

---

*Generated via `/session-wrap`.*
