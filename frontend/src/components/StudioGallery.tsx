import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { api, type GalleryRun } from "@/lib/api";
import { formatBytes } from "@/lib/utils";

/** Classic list + detail used on the Studio tab. */
export function StudioGallery({ refreshKey = 0 }: { refreshKey?: number }) {
  const [runs, setRuns] = useState<GalleryRun[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const data = await api.gallery(40);
        if (!alive) return;
        setRuns(data.runs);
        setErr(null);
        setSelected((prev) => {
          if (prev && data.runs.some((r) => r.run_id === prev)) return prev;
          return data.runs[0]?.run_id ?? null;
        });
      } catch (e) {
        if (alive) setErr(String(e));
      }
    };
    load();
    const id = setInterval(load, 4000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [refreshKey]);

  useEffect(() => {
    if (!selected) {
      setDetail(null);
      return;
    }
    let alive = true;
    api
      .run(selected)
      .then((d) => {
        if (alive) setDetail(d);
      })
      .catch((e) => {
        if (alive) setErr(String(e));
      });
    return () => {
      alive = false;
    };
  }, [selected]);

  const postBody =
    String(detail?.stream_slug || detail?.caption || "").trim() ||
    String(detail?.events || "")
      .split("\n")[0]
      ?.replace(/^[-•]\s*/, "")
      .trim() ||
    "";
  const hasImage =
    !!detail?.has_image || !!runs.find((r) => r.run_id === selected)?.has_image;

  const copyPost = async () => {
    if (!postBody) return;
    await navigator.clipboard.writeText(postBody);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <Card className="lg:col-span-1">
        <CardTitle>Gallery ({runs.length})</CardTitle>
        {err && <p className="text-xs text-bad mb-2">{err}</p>}
        <div className="space-y-1 max-h-[32rem] overflow-y-auto">
          {runs.length === 0 && (
            <p className="text-xs text-muted">No runs yet. Hit Generate.</p>
          )}
          {runs.map((r) => (
            <button
              key={r.run_id}
              type="button"
              onClick={() => setSelected(r.run_id)}
              className={`w-full text-left px-2 py-2 rounded border text-xs transition ${
                selected === r.run_id
                  ? "border-accent bg-accent/10"
                  : "border-transparent hover:border-border"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <code>{r.run_id}</code>
                <Badge
                  tone={
                    r.status === "complete"
                      ? "ok"
                      : r.status === "failed"
                        ? "bad"
                        : r.status === "running"
                          ? "accent"
                          : "neutral"
                  }
                >
                  {r.status}
                </Badge>
              </div>
              <div className="text-muted mt-0.5">
                {r.style_label ?? r.style_id}
                {r.dry_run ? " · dry" : ""}
              </div>
            </button>
          ))}
        </div>
      </Card>

      <Card className="lg:col-span-2">
        <CardTitle>Piece</CardTitle>
        {!selected && <p className="text-xs text-muted">Select a run.</p>}
        {selected && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="text-muted">Run ID</span>
              <code className="px-2 py-0.5 rounded border border-border bg-bg text-accent">
                {selected}
              </code>
              {detail?.style_label != null && (
                <Badge tone="accent">{String(detail.style_label)}</Badge>
              )}
              {detail?.events_source != null && (
                <span className="text-muted">source {String(detail.events_source)}</span>
              )}
              {detail?.news_lane != null && (
                <span className="text-muted">lane {String(detail.news_lane)}</span>
              )}
            </div>

            {hasImage ? (
              <a href={api.imageUrl(selected)} target="_blank" rel="noreferrer">
                <img
                  src={api.imageUrl(selected)}
                  alt={`Planet Hack ${selected}`}
                  className="w-full max-h-[28rem] object-contain object-center rounded border border-border bg-bg"
                />
              </a>
            ) : (
              <div className="h-48 flex items-center justify-center border border-dashed border-border rounded text-muted text-sm">
                No image yet
              </div>
            )}

            <div className="flex flex-wrap gap-2 items-center">
              <Button
                variant="ghost"
                onClick={() => window.open(api.imageUrl(selected), "_blank")}
                disabled={!hasImage}
              >
                Open / download PNG
              </Button>
              <Button variant="ghost" onClick={copyPost} disabled={!postBody}>
                {copied ? "Copied" : "Copy post"}
              </Button>
              <span className="text-xs text-muted">
                Download as planethack_{selected}.png
              </span>
            </div>

            {postBody && (
              <div>
                <div className="text-xs text-muted mb-1">
                  Generative Stream (X post · {postBody.length}/280)
                </div>
                <p className="text-sm border border-border rounded p-2 bg-bg leading-relaxed">
                  {postBody}
                </p>
              </div>
            )}

            {detail?.events != null && (
              <div>
                <div className="text-xs text-muted mb-1">Wire pack (local)</div>
                <pre className="text-xs border border-border rounded p-2 bg-bg whitespace-pre-wrap max-h-28 overflow-y-auto">
                  {String(detail.events)}
                </pre>
              </div>
            )}

            {!!detail?.has_field && selected && (
              <details>
                <summary className="text-xs text-muted cursor-pointer">
                  Kaleidoscope field (stream DNA)
                </summary>
                <a
                  href={api.fieldUrl(selected)}
                  target="_blank"
                  rel="noreferrer"
                  className="block mt-1"
                >
                  <img
                    src={api.fieldUrl(selected)}
                    alt={`Ring field ${selected}`}
                    className="w-full max-h-40 object-contain rounded border border-border bg-bg"
                  />
                </a>
              </details>
            )}

            {detail?.art_brief != null && (
              <details>
                <summary className="text-xs text-muted cursor-pointer">
                  Raster program
                </summary>
                <pre className="text-xs border border-border rounded p-2 bg-bg whitespace-pre-wrap mt-1 max-h-40 overflow-y-auto">
                  {String(detail.art_brief)}
                </pre>
              </details>
            )}

            <div className="text-xs text-muted flex flex-wrap gap-3">
              <span>run {selected}</span>
              {detail?.latency_ms != null && <span>{String(detail.latency_ms)} ms</span>}
              {detail?.egress_bytes != null && (
                <span>egress {formatBytes(Number(detail.egress_bytes))}</span>
              )}
              {detail?.image_model != null && <span>model {String(detail.image_model)}</span>}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
