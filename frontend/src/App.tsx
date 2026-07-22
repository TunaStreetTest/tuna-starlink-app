import { useState } from "react";

import { Gallery } from "@/components/Gallery";
import { GeneratePanel } from "@/components/GeneratePanel";
import { HealthBar } from "@/components/HealthBar";
import { StarlinkPanel } from "@/components/StarlinkPanel";
import { StudioGallery } from "@/components/StudioGallery";
import { cn } from "@/lib/utils";

type Tab = "studio" | "gallery";

export default function App() {
  const [tab, setTab] = useState<Tab>("studio");
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="min-h-full flex flex-col">
      <HealthBar />
      <nav className="flex items-center gap-1 px-4 border-b border-border bg-panel">
        {(
          [
            { id: "studio" as Tab, label: "Studio" },
            { id: "gallery" as Tab, label: "Gallery" },
          ] as const
        ).map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "px-3 py-2 text-sm border-b-2 -mb-px transition-colors",
              tab === t.id
                ? "border-accent text-text"
                : "border-transparent text-muted hover:text-text",
            )}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <main className="flex-1 p-4 max-w-[1400px] mx-auto w-full space-y-4">
        {tab === "studio" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <GeneratePanel onStarted={() => setRefreshKey((k) => k + 1)} />
            <StarlinkPanel />
            <div className="lg:col-span-2">
              <StudioGallery refreshKey={refreshKey} />
            </div>
          </div>
        )}
        {tab === "gallery" && <Gallery refreshKey={refreshKey} />}
      </main>
      <footer className="px-4 py-2 border-t border-border text-xs text-muted">
        Planet Hack · world events as 3D digital infiltration · Grok / xAI Imagine
      </footer>
    </div>
  );
}
