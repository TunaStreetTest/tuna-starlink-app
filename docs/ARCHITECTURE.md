# Architecture — TunaStarLink / Planet Hack

```
┌─────────────────────────────────────────────┐
│  Beelink TunaStarlink (Windows + Starlink)  │
│                                             │
│   Browser ──► TunaStarLink App (:8091)      │
│                 │                           │
│                 ├─ News stream (RSS → disk) │
│                 ├─ Grok chat (xAI cloud)    │
│                 ├─ Imagine   (xAI cloud)    │
│                 ├─ X publish (@tunastarlink)│
│                 └─ ./art  (local disk)      │
│                                             │
│   Optional: Lemonade :13305 (text only)     │
└─────────────────────────────────────────────┘
              │  small HTTPS
              ▼
         api.x.ai  +  api.x.com
```

## Design rules

1. **Cloud for images** — one PNG down per run over Starlink; no local diffusion weights.
2. **Local gallery** — PNG + atomic JSON sidecars under `ART_STORAGE_PATH`.
3. **News as a stream** — RSS injects; each run *taps* unconsumed headlines only.
4. **X first-class** — caption + one news-keyword reply; URLs stored on the run.

## Runtime pieces

| Piece | Tech |
|---|---|
| API | FastAPI + uvicorn |
| UI | Vite + React + Tailwind |
| Chat / Imagine | OpenAI-compatible client → `https://api.x.ai/v1` |
| X | tweepy OAuth 1.0a |
| Scheduler | APScheduler (hourly, random style) |
| Package | Docker Compose single service |

## Data per run

```
art/<run_id>/
  art.png
  meta.json    # events, art_brief, caption, x_url, x_replies, …
art/.news_stream.json   # durable news stream (gitignored)
```

Downloads use `planethack_<run_id>.png`.  
`meta.json` is written via temp-file + `os.replace` (atomic).
