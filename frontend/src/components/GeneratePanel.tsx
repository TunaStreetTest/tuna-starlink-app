import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { api, type PipelineStatus, type Style } from "@/lib/api";
import { formatBytes } from "@/lib/utils";

export function GeneratePanel({ onStarted }: { onStarted?: () => void }) {
  const [styles, setStyles] = useState<Style[]>([]);
  const [style, setStyle] = useState<string>("");
  const [pipe, setPipe] = useState<PipelineStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const refresh = async () => {
    try {
      const [s, p] = await Promise.all([api.styles(), api.pipeline()]);
      setStyles(s.styles);
      setPipe(p);
      if (!style && s.styles.length) setStyle(p.default_style || s.styles[0].id);
    } catch (e) {
      setErr(String(e));
    }
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 2500);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const running = pipe?.current?.status === "running";

  const onGenerate = async () => {
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const res = await api.generate(style || undefined, false);
      setMsg(res.message ?? "started");
      onStarted?.();
      await refresh();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };

  const cur = pipe?.current;

  return (
    <Card>
      <CardTitle>Generate</CardTitle>
      <p className="text-xs text-muted mb-3">
        World events → Grok art director → Imagine → gallery. Series look: 3D digital
        “inside the machine / hacking the planet.”
      </p>

      <label className="block text-xs text-muted mb-1">Style</label>
      <select
        className="w-full mb-3 bg-bg border border-border rounded px-2 py-1.5 text-sm"
        value={style}
        onChange={(e) => setStyle(e.target.value)}
        disabled={running || busy}
      >
        {styles.map((s) => (
          <option key={s.id} value={s.id}>
            {s.label}
          </option>
        ))}
      </select>
      {styles.find((s) => s.id === style)?.description && (
        <p className="text-xs text-muted mb-3">
          {styles.find((s) => s.id === style)?.description}
        </p>
      )}

      <div className="flex items-center gap-2 mb-3">
        <Button variant="accent" onClick={onGenerate} disabled={busy || running}>
          {running ? "Generating…" : "Run Planet Hack"}
        </Button>
        {pipe?.dry_run && <Badge tone="warn">DRY_RUN</Badge>}
        {running && cur?.phase != null && (
          <Badge tone="accent">phase: {String(cur.phase)}</Badge>
        )}
      </div>

      {err && <p className="text-xs text-bad mb-2">{err}</p>}
      {msg && !err && <p className="text-xs text-ok mb-2">{msg}</p>}

      {cur && (
        <div className="text-xs space-y-1 border-t border-border pt-3 mt-2">
          <div className="flex gap-2 flex-wrap">
            <span className="text-muted">last:</span>
            <code>{String(cur.run_id ?? "—")}</code>
            <Badge
              tone={
                cur.status === "complete"
                  ? "ok"
                  : cur.status === "failed"
                    ? "bad"
                    : cur.status === "running"
                      ? "accent"
                      : "neutral"
              }
            >
              {String(cur.status)}
            </Badge>
          </div>
          {cur.latency_ms != null && (
            <div className="text-muted">latency {String(cur.latency_ms)} ms</div>
          )}
          {cur.egress_bytes != null && (
            <div className="text-muted">
              image egress {formatBytes(Number(cur.egress_bytes))} (Starlink-sensitive)
            </div>
          )}
          {cur.error != null && cur.error !== "" && (
            <div className="text-bad break-words">{String(cur.error)}</div>
          )}
        </div>
      )}
    </Card>
  );
}
