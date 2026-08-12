import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { api, type GalleryRun } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";

type FsEl = HTMLElement & {
  webkitRequestFullscreen?: () => Promise<void> | void;
};
type FsDoc = Document & {
  webkitFullscreenElement?: Element | null;
  webkitExitFullscreen?: () => Promise<void> | void;
};

function fsElement(): Element | null {
  const d = document as FsDoc;
  return document.fullscreenElement ?? d.webkitFullscreenElement ?? null;
}

async function requestFs(el: HTMLElement): Promise<void> {
  const node = el as FsEl;
  if (node.requestFullscreen) {
    await node.requestFullscreen();
    return;
  }
  if (node.webkitRequestFullscreen) {
    await node.webkitRequestFullscreen();
  }
}

async function exitFs(): Promise<void> {
  if (!fsElement()) return;
  const d = document as FsDoc;
  if (document.exitFullscreen) {
    await document.exitFullscreen();
    return;
  }
  if (d.webkitExitFullscreen) await d.webkitExitFullscreen();
}

/** Tiled gallery with detail modal (includes Post to X). Used on Studio. */
export function Gallery({ refreshKey = 0 }: { refreshKey?: number }) {
  const [runs, setRuns] = useState<GalleryRun[]>([]);
  const [modalId, setModalId] = useState<string | null>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [xBusy, setXBusy] = useState(false);
  const [xMsg, setXMsg] = useState<string | null>(null);
  const [xReady, setXReady] = useState(false);
  const stageRef = useRef<HTMLDivElement>(null);

  const stack = useMemo(() => runs.filter((r) => r.has_image), [runs]);
  const stackIdx = useMemo(
    () => (modalId ? stack.findIndex((r) => r.run_id === modalId) : -1),
    [stack, modalId],
  );
  const canPrev = stackIdx > 0;
  const canNext = stackIdx >= 0 && stackIdx < stack.length - 1;

  const goStack = useCallback(
    (dir: -1 | 1) => {
      const next = stackIdx + dir;
      if (next < 0 || next >= stack.length) return;
      setModalId(stack[next].run_id);
    },
    [stack, stackIdx],
  );

  const openFullscreen = useCallback(() => {
    const el = stageRef.current;
    if (el) {
      // Must be visible in this user-gesture turn or requestFullscreen paints black.
      el.classList.remove("invisible", "pointer-events-none");
      void requestFs(el).catch(() => {
        /* overlay still covers the viewport if the API is blocked */
      });
    }
    setFullscreen(true);
  }, []);

  const closeFullscreen = useCallback(() => {
    setFullscreen(false);
    void exitFs().catch(() => undefined);
  }, []);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const [data, pub] = await Promise.all([
          api.gallery(60),
          api.publishStatus().catch(() => null),
        ]);
        if (!alive) return;
        setRuns(data.runs);
        setErr(null);
        if (pub) setXReady(!!pub.credentials_ready);
      } catch (e) {
        if (alive) setErr(String(e));
      }
    };
    load();
    const id = setInterval(load, 5000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [refreshKey]);

  useEffect(() => {
    if (!modalId) {
      setDetail(null);
      setXMsg(null);
      setFullscreen(false);
      void exitFs().catch(() => undefined);
      return;
    }
    let alive = true;
    setDetail(null);
    api
      .run(modalId)
      .then((d) => {
        if (alive) setDetail(d);
      })
      .catch((e) => {
        if (alive) setErr(String(e));
      });
    return () => {
      alive = false;
    };
  }, [modalId]);

  // Escape: leave fullscreen first, then close modal. Arrows walk the stack.
  useEffect(() => {
    if (!modalId) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (fullscreen || fsElement()) closeFullscreen();
        else setModalId(null);
        return;
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goStack(-1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goStack(1);
      } else if ((e.key === "f" || e.key === "F") && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        if (fullscreen || fsElement()) closeFullscreen();
        else openFullscreen();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [modalId, fullscreen, goStack, openFullscreen, closeFullscreen]);

  // Stay in sync if the user hits Esc / the browser exits native fullscreen.
  useEffect(() => {
    const onFs = () => {
      if (!fsElement()) setFullscreen(false);
    };
    document.addEventListener("fullscreenchange", onFs);
    document.addEventListener("webkitfullscreenchange", onFs);
    return () => {
      document.removeEventListener("fullscreenchange", onFs);
      document.removeEventListener("webkitfullscreenchange", onFs);
    };
  }, []);

  // Preload neighbors so left/right in fullscreen feels instant.
  useEffect(() => {
    if (!fullscreen || stackIdx < 0) return;
    for (const i of [stackIdx - 1, stackIdx + 1]) {
      const run = stack[i];
      if (!run) continue;
      const img = new Image();
      img.src = api.imageUrl(run.run_id);
    }
  }, [fullscreen, stack, stackIdx]);

  // Main X body = Generative Stream (single headline), not a mood poem.
  const postBody =
    String(detail?.stream_slug || detail?.caption || "").trim() ||
    String(detail?.events || "")
      .split("\n")[0]
      ?.replace(/^[-•]\s*/, "")
      .trim() ||
    "";
  const hasImage = !!detail?.has_image || !!runs.find((r) => r.run_id === modalId)?.has_image;
  const alreadyPosted = !!detail?.x_post_id;

  const copyPost = async () => {
    if (!postBody) return;
    await navigator.clipboard.writeText(postBody);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const postToX = async () => {
    if (!modalId) return;
    setXBusy(true);
    setXMsg(null);
    try {
      const res = await api.publishX(modalId, false);
      setXMsg(
        res.already_posted ? `Already posted: ${res.x_url}` : `Posted: ${res.x_url}`,
      );
      const d = await api.run(modalId);
      setDetail(d);
    } catch (e) {
      setXMsg(String(e));
    } finally {
      setXBusy(false);
    }
  };

  return (
    <>
      <Card>
        <div className="flex items-center justify-between gap-2 mb-3">
          <CardTitle className="mb-0">Gallery ({runs.length})</CardTitle>
          {err && <p className="text-xs text-bad">{err}</p>}
        </div>
        <p className="text-xs text-muted mb-3">
          Click a tile for details. Fullscreen takes the whole monitor —
          ← → walk the stack.
        </p>

        {runs.length === 0 && (
          <p className="text-xs text-muted">No runs yet. Hit Run Planet Hack above.</p>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-3">
          {runs.map((r) => (
            <button
              key={r.run_id}
              type="button"
              onClick={() => setModalId(r.run_id)}
              className={cn(
                "group relative aspect-square rounded-md border overflow-hidden bg-bg text-left transition",
                "border-border hover:border-accent hover:ring-1 hover:ring-accent/30",
              )}
            >
              {r.has_image ? (
                <img
                  src={api.imageUrl(r.run_id)}
                  alt={r.style_label ?? r.run_id}
                  className="h-full w-full object-cover"
                  loading="lazy"
                />
              ) : (
                <div className="h-full w-full flex items-center justify-center text-muted text-xs p-2">
                  {r.status}
                </div>
              )}
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 to-transparent p-2 pt-8">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-[10px] text-white/90 truncate">
                    {r.style_label ?? r.style_id}
                  </span>
                  {r.dry_run && <Badge tone="warn">dry</Badge>}
                </div>
                <div className="text-[9px] text-white/60 font-mono truncate mt-0.5">
                  {r.run_id}
                </div>
              </div>
            </button>
          ))}
        </div>
      </Card>

      {modalId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70"
          onClick={() => setModalId(null)}
          role="presentation"
        >
          <div
            className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-lg border border-border bg-panel shadow-xl"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="sticky top-0 z-10 flex items-center justify-between gap-2 px-4 py-3 border-b border-border bg-panel/95 backdrop-blur">
              <div>
                <div className="text-sm font-medium">
                  {(detail?.style_label as string) ||
                    runs.find((r) => r.run_id === modalId)?.style_label ||
                    "Piece"}
                </div>
                <div className="flex flex-wrap items-center gap-2 mt-0.5">
                  <span className="text-[10px] text-muted">Run ID</span>
                  <code className="text-[10px] text-accent font-mono">{modalId}</code>
                  {detail?.events_source != null && (
                    <span className="text-[10px] text-muted">
                      · {String(detail.events_source)}
                    </span>
                  )}
                </div>
              </div>
              <Button variant="ghost" onClick={() => setModalId(null)}>
                Close
              </Button>
            </div>

            <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                {hasImage ? (
                  <button
                    type="button"
                    onClick={openFullscreen}
                    className="block w-full group relative"
                    title="Fullscreen"
                  >
                    <img
                      src={api.imageUrl(modalId)}
                      alt={`Planet Hack ${modalId}`}
                      className="w-full max-h-[60vh] object-contain rounded border border-border bg-bg"
                    />
                    <span className="pointer-events-none absolute bottom-2 right-2 text-[10px] uppercase tracking-wide text-white/80 bg-black/55 px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition">
                      Fullscreen
                    </span>
                  </button>
                ) : (
                  <div className="h-48 flex items-center justify-center border border-dashed border-border rounded text-muted text-sm">
                    {detail ? "No image" : "Loading…"}
                  </div>
                )}
              </div>

              <div className="space-y-3">
                {postBody && (
                  <div>
                    <div className="text-xs text-muted mb-1">
                      Generative Stream (X post · {postBody.length}/280)
                    </div>
                    <p className="text-sm border border-border rounded p-3 bg-bg leading-relaxed">
                      {postBody}
                    </p>
                  </div>
                )}

                {detail?.events != null && (
                  <div>
                    <div className="text-xs text-muted mb-1">Wire pack (local)</div>
                    <pre className="text-xs border border-border rounded p-2 bg-bg whitespace-pre-wrap max-h-24 overflow-y-auto">
                      {String(detail.events)}
                    </pre>
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="ghost"
                    onClick={openFullscreen}
                    disabled={!hasImage}
                  >
                    Fullscreen
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => window.open(api.imageUrl(modalId), "_blank")}
                    disabled={!hasImage}
                  >
                    Open PNG
                  </Button>
                  <Button variant="ghost" onClick={copyPost} disabled={!postBody}>
                    {copied ? "Copied" : "Copy post"}
                  </Button>
                  <Button
                    variant="accent"
                    onClick={() => {
                      if (alreadyPosted && detail?.x_url) {
                        window.open(String(detail.x_url), "_blank");
                        return;
                      }
                      void postToX();
                    }}
                    disabled={!hasImage || xBusy || !!detail?.dry_run}
                  >
                    {xBusy
                      ? "Posting…"
                      : alreadyPosted
                        ? "Open X post"
                        : xReady
                          ? "Post to X"
                          : "Post to X (set keys)"}
                  </Button>
                </div>

                {alreadyPosted && detail?.x_url != null && (
                  <a
                    className="text-xs text-accent underline break-all block"
                    href={String(detail.x_url)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {String(detail.x_url)}
                  </a>
                )}
                {xMsg && (
                  <p
                    className={cn(
                      "text-xs break-all",
                      xMsg.startsWith("Posted") || xMsg.startsWith("Already")
                        ? "text-ok"
                        : "text-bad",
                    )}
                  >
                    {xMsg}
                  </p>
                )}
                <p className="text-xs text-muted">
                  X: image + Generative Stream headline (no hashtags, no reply)
                </p>

                {(detail?.has_field ||
                  runs.find((r) => r.run_id === modalId)?.has_field) && (
                  <details>
                    <summary className="text-xs text-muted cursor-pointer">
                      Kaleidoscope field (stream DNA)
                    </summary>
                    <a
                      href={api.fieldUrl(modalId)}
                      target="_blank"
                      rel="noreferrer"
                      className="block mt-1"
                    >
                      <img
                        src={api.fieldUrl(modalId)}
                        alt={`Ring field ${modalId}`}
                        className="w-full max-h-48 object-contain rounded border border-border bg-bg"
                      />
                    </a>
                  </details>
                )}

                {detail?.art_brief != null && (
                  <details>
                    <summary className="text-xs text-muted cursor-pointer">
                      Raster program (local only)
                    </summary>
                    <pre className="text-xs border border-border rounded p-2 bg-bg whitespace-pre-wrap mt-1 max-h-32 overflow-y-auto">
                      {String(detail.art_brief)}
                    </pre>
                  </details>
                )}

                {detail?.events != null && (
                  <details>
                    <summary className="text-xs text-muted cursor-pointer">
                      Source events (local only)
                    </summary>
                    <pre className="text-xs border border-border rounded p-2 bg-bg whitespace-pre-wrap mt-1 max-h-28 overflow-y-auto">
                      {String(detail.events)}
                    </pre>
                  </details>
                )}

                <div className="text-xs text-muted flex flex-wrap gap-3">
                  {detail?.latency_ms != null && <span>{String(detail.latency_ms)} ms</span>}
                  {detail?.egress_bytes != null && (
                    <span>{formatBytes(Number(detail.egress_bytes))}</span>
                  )}
                  {detail?.image_model != null && <span>{String(detail.image_model)}</span>}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Always mounted while a piece is open so requestFullscreen stays a user gesture. */}
      {modalId && hasImage && (
        <div
          ref={stageRef}
          className={cn(
            "fixed inset-0 z-[60] h-screen w-screen bg-black flex items-center justify-center",
            fullscreen ? "visible" : "invisible pointer-events-none",
          )}
          role="dialog"
          aria-modal={fullscreen}
          aria-label="Fullscreen gallery"
          onClick={closeFullscreen}
        >
          <img
            src={api.imageUrl(modalId)}
            alt={`Planet Hack ${modalId}`}
            className="h-full w-full object-contain select-none"
            onClick={(e) => e.stopPropagation()}
          />

          <button
            type="button"
            aria-label="Previous image"
            disabled={!canPrev}
            onClick={(e) => {
              e.stopPropagation();
              goStack(-1);
            }}
            className={cn(
              "absolute left-3 top-1/2 -translate-y-1/2 h-12 w-12 rounded-full",
              "border border-white/25 bg-black/50 text-white text-2xl leading-none",
              "hover:bg-black/75 hover:border-white/50 transition",
              "disabled:opacity-25 disabled:cursor-not-allowed",
            )}
          >
            ‹
          </button>
          <button
            type="button"
            aria-label="Next image"
            disabled={!canNext}
            onClick={(e) => {
              e.stopPropagation();
              goStack(1);
            }}
            className={cn(
              "absolute right-3 top-1/2 -translate-y-1/2 h-12 w-12 rounded-full",
              "border border-white/25 bg-black/50 text-white text-2xl leading-none",
              "hover:bg-black/75 hover:border-white/50 transition",
              "disabled:opacity-25 disabled:cursor-not-allowed",
            )}
          >
            ›
          </button>

          <button
            type="button"
            aria-label="Exit fullscreen"
            onClick={(e) => {
              e.stopPropagation();
              closeFullscreen();
            }}
            className="absolute top-3 right-3 px-3 py-1.5 rounded text-sm text-white/90 border border-white/25 bg-black/50 hover:bg-black/75"
          >
            Close
          </button>

          <div
            className="absolute bottom-3 left-1/2 -translate-x-1/2 max-w-[90vw] px-3 py-1.5 rounded bg-black/60 text-white/85 text-xs font-mono text-center"
            onClick={(e) => e.stopPropagation()}
          >
            {(detail?.style_label as string) ||
              runs.find((r) => r.run_id === modalId)?.style_label ||
              "Piece"}
            {" · "}
            {modalId}
            {stackIdx >= 0 && (
              <span className="text-white/55">
                {" "}
                · {stackIdx + 1} / {stack.length}
              </span>
            )}
            <span className="hidden sm:inline text-white/40">
              {" "}
              · ← → · Esc
            </span>
          </div>
        </div>
      )}
    </>
  );
}
