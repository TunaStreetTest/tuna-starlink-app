import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { api, type BatchPanel, type GalleryRun, type PipelineStatus, type Style } from "@/lib/api";

function latestPlate(runs: GalleryRun[], styleId: string): GalleryRun | undefined {
  return runs.find((run) => run.style_id === styleId && run.has_image);
}

function panelOf(pipe: PipelineStatus | null, styleId: string): BatchPanel | null {
  return pipe?.batch?.panels?.[styleId] ?? null;
}

export function GeneratePanel({ onStarted }: { onStarted?: () => void }) {
  const [styles, setStyles] = useState<Style[]>([]);
  const [runs, setRuns] = useState<GalleryRun[]>([]);
  const [pipe, setPipe] = useState<PipelineStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, p, g] = await Promise.all([
        api.styles(),
        api.pipeline(),
        api.gallery(200),
      ]);
      setStyles(s.styles);
      setPipe(p);
      setRuns(g.runs);
      setErr(null);
    } catch (e) {
      setErr(String(e));
    }
  }, []);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      if (!alive) return;
      await refresh();
    };
    tick();
    const id = setInterval(tick, 2500);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [refresh]);

  const batchOn = !!pipe?.batch?.active;
  const running = batchOn || pipe?.current?.status === "running";

  const onGenerate = async () => {
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const res = await api.generateAll();
      setMsg(res.message ?? "queued");
      onStarted?.();
      await refresh();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-5">
        <div>
          <p className="font-mono text-[0.68rem] tracking-[0.24em] uppercase text-accent">
            Planet Hack
          </p>
          <h1 className="mt-1 text-3xl sm:text-4xl font-medium tracking-tight text-text">
            One plate for every type.
          </h1>
          <p className="mt-2 max-w-xl text-sm text-muted font-mono leading-relaxed">
            Generate queues one plate per type, in order. Each panel holds the last
            picture until its turn lands.
          </p>
        </div>
        <div className="flex flex-col items-start gap-2">
          <Button variant="accent" onClick={onGenerate} disabled={busy || running}>
            {running ? "On the wire…" : "Generate"}
          </Button>
          <div className="flex flex-wrap items-center gap-2">
            {pipe?.dry_run && <Badge tone="warn">DRY RUN</Badge>}
            {pipe?.auto_publish && <Badge tone="hot">auto post</Badge>}
          </div>
        </div>
      </div>

      {err && <p className="text-xs font-mono text-bad mb-3">{err}</p>}
      {msg && !err && <p className="text-xs font-mono text-ok mb-3">{msg}</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
        {styles.map((style) => (
          <TypeScreen
            key={style.id}
            style={style}
            panel={panelOf(pipe, style.id)}
            plate={latestPlate(runs, style.id)}
            live={pipe?.current}
          />
        ))}
      </div>
    </section>
  );
}

function TypeScreen({
  style,
  panel,
  plate,
  live,
}: {
  style: Style;
  panel: BatchPanel | null;
  plate: GalleryRun | undefined;
  live: Record<string, unknown> | null | undefined;
}) {
  const liveHere = !!live && String(live.style_id ?? "") === style.id;
  const liveStatus = liveHere ? String(live?.status ?? "") : "";
  const status = liveStatus === "running" ? "running" : panel?.status || "idle";
  const phase =
    liveStatus === "running" ? String(live?.phase ?? "") : String(panel?.phase ?? "");
  const freshId =
    status === "complete" ? panel?.run_id || (liveHere ? String(live?.run_id ?? "") : "") : "";
  const imageId = freshId || plate?.run_id || "";
  const failed = status === "failed" || liveStatus === "failed";
  const errorText = String(panel?.error || (liveHere ? live?.error ?? "" : ""));

  return (
    <article className="rounded-[10px] border border-accent/35 bg-[#100c0a] p-2 shadow-[0_0_28px_rgba(126,240,255,0.06)]">
      <div className="crt relative aspect-video overflow-hidden bg-black">
        {imageId ? (
          <img
            src={api.imageUrl(imageId)}
            alt={style.label}
            className="absolute inset-0 h-full w-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="font-mono text-[0.68rem] tracking-[0.22em] uppercase text-accent/80">
              No signal
            </span>
          </div>
        )}
        <div className="absolute inset-x-0 top-0 z-10 flex items-start justify-between gap-2 p-2">
          <span className="font-mono text-[0.62rem] tracking-[0.18em] uppercase text-accent bg-black/55 px-1.5 py-0.5">
            {style.label}
          </span>
          {style.lane && (
            <span className="font-mono text-[0.62rem] tracking-[0.14em] uppercase text-hot bg-black/55 px-1.5 py-0.5">
              {style.lane}
            </span>
          )}
        </div>
        <div className="absolute inset-x-0 bottom-0 z-10 p-2 pt-8 bg-gradient-to-t from-black/80 to-transparent">
          <p className="font-mono text-[0.68rem] tracking-[0.12em] uppercase text-[#d8fbff]">
            {status === "running"
              ? phase || "running"
              : failed
                ? "failed"
                : status === "queued"
                  ? "queued"
                  : status === "complete"
                    ? "plate in"
                    : plate
                      ? "last plate"
                      : "standing by"}
          </p>
        </div>
      </div>
      <p className="mt-2 px-1 text-[0.78rem] leading-snug text-[#c9d2d8] line-clamp-3">
        {style.description}
      </p>
      {failed && errorText && (
        <p className="mt-1 px-1 text-[0.68rem] font-mono text-bad line-clamp-3">{errorText}</p>
      )}
    </article>
  );
}
