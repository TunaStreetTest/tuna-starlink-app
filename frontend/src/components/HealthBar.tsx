import { useEffect, useState } from "react";

import { Dot } from "@/components/ui/Badge";
import { api, type Health } from "@/lib/api";
import { cn } from "@/lib/utils";

export function HealthBar() {
  const [h, setH] = useState<Health | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const data = await api.health();
        if (alive) {
          setH(data);
          setErr(null);
        }
      } catch (e) {
        if (alive) setErr(String(e));
      }
    };
    tick();
    const id = setInterval(tick, 30000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const svc = h?.services ?? {};
  const entries = Object.entries(svc);

  return (
    <header className="flex flex-wrap items-center gap-3 px-4 py-2 border-b border-border bg-panel/80">
      <div className="flex items-center gap-2 mr-2">
        <span className="text-accent font-semibold tracking-wide">TunaStarLink</span>
        <span className="text-muted text-xs">Planet Hack</span>
      </div>
      {err && <span className="text-bad text-xs">health: {err}</span>}
      {entries.map(([name, s]) => (
        <span key={name} className="flex items-center gap-1.5 text-xs text-muted">
          <Dot tone={s.ok ? "ok" : "bad"} />
          {name}
        </span>
      ))}
      {h?.services?.xai && (
        <span
          className={cn(
            "text-xs px-2 py-0.5 rounded border",
            h.services.xai.dry_run
              ? "border-warn/40 text-warn"
              : "border-accent/40 text-accent",
          )}
        >
          {h.services.xai.dry_run ? "DRY_RUN" : "LIVE xAI"}
        </span>
      )}
    </header>
  );
}
