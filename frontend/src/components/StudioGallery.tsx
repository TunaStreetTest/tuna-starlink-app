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

  const caption = (detail?.caption as string) || "";
  const hasImage =
    !!detail?.has_image || !!runs.find((r) => r.run_id === selected)?.has_image;

  const copyCaption = async () => {
    if (!caption) return;
    await navigator.clipboard.writeText(caption);
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
            {hasImage ? (
              <a href={api.imageUrl(selected)} target="_blank" rel="noreferrer">
                <img
                  src={api.imageUrl(selected)}
                  alt={`Planet Hack ${selected}`}
                  className="w-full max-h-[28rem] object-contain rounded border border-border bg-bg"
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
              <Button variant="ghost" onClick={copyCaption} disabled={!caption}>
                {copied ? "Caption copied" : "Copy caption"}
              </Button>
              <span className="text-xs text-muted">
                Post to @tunastarlink when it looks cool enough.
              </span>
            </div>

            {caption && (
              <div>
                <div className="text-xs text-muted mb-1">Caption</div>
                <p className="text-sm border border-border rounded p-2 bg-bg leading-relaxed">
                  {caption}
                </p>
              </div>
            )}

            {detail?.art_brief != null && (
              <div>
                <div className="text-xs text-muted mb-1">Art director brief</div>
                <pre className="text-xs border border-border rounded p-2 bg-bg whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {String(detail.art_brief)}
                </pre>
              </div>
            )}

            {detail?.events != null && (
              <details>
                <summary className="text-xs text-muted cursor-pointer">
                  Source events
                </summary>
                <pre className="text-xs border border-border rounded p-2 bg-bg whitespace-pre-wrap mt-1 max-h-32 overflow-y-auto">
                  {String(detail.events)}
                </pre>
              </details>
            )}

            <div className="text-xs text-muted flex flex-wrap gap-3">
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
