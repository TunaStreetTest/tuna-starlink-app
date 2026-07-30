# Planet Hack — creative brief (locked)

## Series

**Name:** Planet Hack  
**Account target:** @tunastarlink  
**Tagline:** World events, rendered as a 3D digital infiltration of the planetary mainframe.

## Aesthetic (non-negotiable)

- Hacker-movie climax: **inside the computer / hacking the planet**
- Quality bar: best Grok Imagine showcase stills — **one** impossible poetic architecture,
  photoreal materials, dual warm/cool light, epic scale, atmospheric depth
- Neon accents (cyan / magenta / acid-green) subordinate to materials + composition
- **Not:** oil paint, neon lightning weather, lava, scrapyard soup, people, readable UI text

## Pipeline

```
1. Grok news desk     → event bullets
2. Grok 4.5 art dir   → SHOT paragraph (one poetic plate) + light meta
3. Compose            → SHOT leads; short style/hard locks only
4. Imagine            → grok-imagine-image-quality (~$0.05 @ 1K; skip 2K for now)
5. Fast caption       → stream slug
```

## Shot presets

| id | Look |
|---|---|
| `planet-core` | Hero planetary mainframe core (default) |
| `data-tunnel` | Speed-rush packet tunnel |
| `signal-cathedral` | Vertical signal megastructure |
| `rootkit-city` | Dense digital city inside the computer — GPU/CPU/data towers |

## Dry-run honesty

Dry-run never calls Imagine. It draws a local neon grid placeholder and a canned brief so UI/plumbing can be tested for free. **Ignore dry-run PNGs for taste.**

## Cost

Default is `grok-imagine-image-quality` (~$0.05/image at 1K). Optional: `XAI_IMAGE_RESOLUTION=2k` (~$0.07). Fall back to `grok-imagine-image` (~$0.02) only for cheap experiments.
