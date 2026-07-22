# Planet Hack — build stats (this session)

Measured at wrap-up of the Grok Build session that created `tuna-starlink-app` from scratch (2026-07-21/22).

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.5  

---

## Lines of code (repository)

Counted with `wc -l` on tracked product sources (excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`).

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **1,969** |
| Frontend (`frontend/src` — ts/tsx/css) | **1,057** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **109** |
| **Application code subtotal** | **~3,135** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **735** |
| Makefile, Dockerfile, `.env.example`, samples | **129** |
| **All product files** | **~3,999** |

Rough shape: **~3.1k app lines**, **~4.0k with docs**.

### By language (product tree)

| Ext | Lines |
|---|---:|
| `.py` | 1,969 |
| `.tsx` | 936 |
| `.md` | 735 |
| `.ts` | 148 |
| `.yaml` / `.yml` | 109 |
| other (Makefile, Dockerfile, env.example, …) | ~102 |

---

## Session activity (Grok Build signals)

From session telemetry (`signals.json`) at wrap-up:

| Metric | Value |
|---|---:|
| Session duration | **~9,548 s** (~2.65 hours) |
| User messages / turns | **46** |
| Assistant messages | **164** |
| Tool calls | **371** (4 failures) |
| Files touched by agent | **59** |
| Agent lines added (editor telemetry) | **4,680** |
| Agent lines removed | **1** |
| Compactions | **0** |
| Git commits this session (signal counter) | **1+** (more may follow) |

Tools used: `run_terminal_command`, `read_file`, `write`, `search_replace`, `grep`, `list_dir`, `web_fetch`, `todo_write`, `enter_plan_mode` / `exit_plan_mode`, `ask_user_question`, …

---

## Tokens

| What | Value | Notes |
|---|---:|---|
| **Context window size** | **500,000** | Session model window |
| **Context tokens in use (snapshot)** | **~316,480** | ~**63%** of window at wrap-up — *occupancy, not lifetime bill* |
| **Lifetime prompt + completion tokens billed** | **Not exposed** | Runtime does not publish a cumulative in/out meter to the agent |

**How to read this:** `contextTokensUsed` is how full the active window was near the end of the session. Lifetime billed tokens (sum of every turn’s input/output over ~46 turns) is **higher** and only available from your xAI / Grok Build usage dashboard if you need the exact invoice number.

Rough transcript size of stored chat history: ~4.0M characters of JSONL (includes tool payloads) — **not** a reliable billable-token figure.

---

## Product shipped (checklist)

- News stream (RSS inject → tap unconsumed)
- Grok art director + Imagine (16:9)
- Studio + tiled Gallery + modal
- X post to @tunastarlink (caption + news-keyword reply)
- Hourly schedule, random style, optional auto-publish
- Beelink install + style-seed sharing docs
- `planethack_<run_id>.png` downloads

---

*Regenerate tallies anytime:*

```bash
find backend worker scripts -name '*.py' ! -path '*/.venv/*' | xargs wc -l
find frontend/src -type f \( -name '*.tsx' -o -name '*.ts' -o -name '*.css' \) | xargs wc -l
```
