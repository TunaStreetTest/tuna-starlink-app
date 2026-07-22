# Architecture — TunaStarLink (lean)

```
┌─────────────────────────────────────────────┐
│  Beelink TunaStarlink (Windows + Starlink)  │
│                                             │
│   Browser ──► TunaStarLink App (:8091)      │
│                 │                           │
│                 ├─ Grok chat (xAI cloud)    │
│                 ├─ Imagine   (xAI cloud)    │
│                 └─ ./art  (local disk)      │
│                                             │
│   Optional: Lemonade :13305 (text only)     │
└─────────────────────────────────────────────┘
              │  small HTTPS
              ▼
         api.x.ai  +  (you) post PNG to X
```

## Design rules

1. **Cloud for images** — never pull multi-GB diffusion weights over Starlink.
2. **Local for gallery** — PNG + atomic JSON sidecars under `ART_STORAGE_PATH`.
3. **No CSO dependency** for the happy path — Kafka/EFM/NiFi are out of v1.
4. **Manual publish first** — download PNG, copy caption, post as @tunastarlink when proud of it.
5. **cso-operator-app isolation** — different name, different ports, different storage.

## Runtime pieces

| Piece | Tech |
|---|---|
| API | FastAPI + uvicorn |
| UI | Vite + React + Tailwind |
| Chat / Imagine | OpenAI-compatible client → `https://api.x.ai/v1` |
| Scheduler | APScheduler (off by default) |
| Package | Docker Compose single service |

## Data per run

```
art/20260721_210501/
  art.png
  meta.json    # events, prompt, caption, egress_bytes, status, …
```

`meta.json` is written via temp-file + `os.replace` (atomic) so a crash mid-write cannot leave empty/corrupt gallery state.
