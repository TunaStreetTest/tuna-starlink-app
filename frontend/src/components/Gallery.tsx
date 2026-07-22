import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { api, type GalleryRun } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";

/** Tiled gallery page — tiles only; details open in a modal. */
export function Gallery({ refreshKey = 0 }: { refreshKey?: number }) {
  const [runs, setRuns] = useState<GalleryRun[]>([]);
  const [modalId, setModalId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [xBusy, setXBusy] = useState(false);
  const [xMsg, setXMsg] = useState<string | null>(null);
  const [xReady, setXReady] = useState(false);

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

  // Escape closes modal
  useEffect(() => {
    if (!modalId) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setModalId(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [modalId]);

  const caption = (detail?.caption as string) || "";
  const hasImage = !!detail?.has_image || !!runs.find((r) => r.run_id === modalId)?.has_image;
  const alreadyPosted = !!detail?.x_post_id;

  const copyCaption = async () => {
    if (!caption) return;
    await navigator.clipboard.writeText(caption);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const postToX = async () => {
    if (!modalId) return;
    setXBusy(true);
    setXMsg(null);
    try {
      const res = await api.publishX(modalId, true);
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
        <p className="text-xs text-muted mb-3">Click a tile to open details.</p>

        {runs.length === 0 && (
          <p className="text-xs text-muted">No runs yet. Generate from Studio.</p>
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
                  <a href={api.imageUrl(modalId)} target="_blank" rel="noreferrer">
                    <img
                      src={api.imageUrl(modalId)}
                      alt={`Planet Hack ${modalId}`}
                      className="w-full max-h-[60vh] object-contain rounded border border-border bg-bg"
                    />
                  </a>
                ) : (
                  <div className="h-48 flex items-center justify-center border border-dashed border-border rounded text-muted text-sm">
                    {detail ? "No image" : "Loading…"}
                  </div>
                )}
              </div>

              <div className="space-y-3">
                {caption && (
                  <div>
                    <div className="text-xs text-muted mb-1">Caption (main post body)</div>
                    <p className="text-sm border border-border rounded p-3 bg-bg leading-relaxed">
                      {caption}
                    </p>
                  </div>
                )}

                {(detail?.stream_slug != null || detail?.events != null) && (
                  <div>
                    <div className="text-xs text-muted mb-1">Generative Stream (reply)</div>
                    <p className="text-sm border border-border rounded p-3 bg-bg leading-relaxed">
                      Generative Stream:{" "}
                      {String(
                        detail?.stream_slug ||
                          String(detail?.events || "")
                            .split("\n")[0]
                            ?.replace(/^[-•]\s*/, "")
                            .split(" — ")[0] ||
                          "…",
                      )}{" "}
                      {detail?.style_hashtag
                        ? `#${String(detail.style_hashtag)}`
                        : ""}
                    </p>
                  </div>
                )}

                {detail?.events != null && (
                  <div>
                    <div className="text-xs text-muted mb-1">Source (single story)</div>
                    <pre className="text-xs border border-border rounded p-2 bg-bg whitespace-pre-wrap max-h-24 overflow-y-auto">
                      {String(detail.events)}
                    </pre>
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => window.open(api.imageUrl(modalId), "_blank")}
                    disabled={!hasImage}
                  >
                    Open PNG
                  </Button>
                  <Button variant="ghost" onClick={copyCaption} disabled={!caption}>
                    {copied ? "Copied" : "Copy caption"}
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
                  X: caption + #PlanetHack #StyleTag · reply{" "}
                  <code className="text-[10px]">Generative Stream: … #StyleTag</code>
                </p>

                {detail?.art_brief != null && (
                  <details>
                    <summary className="text-xs text-muted cursor-pointer">
                      Art director brief (local only)
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
    </>
  );
}
