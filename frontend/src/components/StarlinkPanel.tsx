import { useEffect, useState } from "react";

import { Card, CardTitle } from "@/components/ui/Card";
import { api, type Health, type PipelineStatus } from "@/lib/api";
import { formatBytes } from "@/lib/utils";

export function StarlinkPanel() {
  const [h, setH] = useState<Health | null>(null);
  const [p, setP] = useState<PipelineStatus | null>(null);

  useEffect(() => {
    const tick = async () => {
      try {
        const [health, pipe] = await Promise.all([api.health(), api.pipeline()]);
        setH(health);
        setP(pipe);
      } catch {
        /* ignore */
      }
    };
    tick();
    const id = setInterval(tick, 5000);
    return () => clearInterval(id);
  }, []);

  const disk = h?.services?.disk;
  const recent = p?.recent ?? [];
  const news = (p as { news_stream?: Record<string, unknown> } | null)?.news_stream;
  const totalEgress = recent.reduce(
    (acc, r) => acc + (typeof r.egress_bytes === "number" ? r.egress_bytes : 0),
    0,
  );

  return (
    <Card>
      <CardTitle>Starlink budget</CardTitle>
      <p className="text-xs text-muted mb-3">
        Starlink-hosted digital series. One cloud image download per run; art stays local.
      </p>
      <dl className="grid grid-cols-2 gap-2 text-xs">
        <dt className="text-muted">Art path</dt>
        <dd className="truncate" title={h?.art_path}>
          {h?.art_path ?? "—"}
        </dd>
        <dt className="text-muted">Runs on disk</dt>
        <dd>{disk?.runs != null ? String(disk.runs) : "—"}</dd>
        <dt className="text-muted">Disk used</dt>
        <dd>{disk?.bytes != null ? formatBytes(Number(disk.bytes)) : "—"}</dd>
        <dt className="text-muted">Recent image egress</dt>
        <dd>{formatBytes(totalEgress)}</dd>
        <dt className="text-muted">Edge text</dt>
        <dd>{p?.edge_text ?? h?.edge_text ?? "—"}</dd>
        <dt className="text-muted">Schedule</dt>
        <dd>
          {p?.schedule_enabled
            ? `${p.schedule_cron ?? "on"}${p.schedule_timezone ? ` (${p.schedule_timezone})` : ""}`
            : "off (manual generate only)"}
        </dd>
        <dt className="text-muted">Auto publish</dt>
        <dd>{p?.auto_publish ? "on → X after each run" : "off"}</dd>
        <dt className="text-muted">X account</dt>
        <dd>{p?.x_account ?? "@tunastarlink"}</dd>
        <dt className="text-muted">News stream</dt>
        <dd>
          {news
            ? `${String(news.unconsumed ?? "?")} fresh / ${String(news.total ?? "?")} total · ${String(news.taps ?? 0)} taps`
            : "—"}
        </dd>
      </dl>
    </Card>
  );
}
