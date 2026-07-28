import { useState } from "react";

import { Gallery } from "@/components/Gallery";
import { GeneratePanel } from "@/components/GeneratePanel";
import { HealthBar } from "@/components/HealthBar";
import { StarlinkPanel } from "@/components/StarlinkPanel";

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="min-h-full flex flex-col">
      <HealthBar />
      <header className="px-4 py-2 border-b border-border bg-panel">
        <h1 className="text-sm font-medium text-text">Studio</h1>
        <p className="text-xs text-muted">
          Generate · browse · Post to X — all in one place
        </p>
      </header>
      <main className="flex-1 p-4 max-w-[1400px] mx-auto w-full space-y-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <GeneratePanel onStarted={() => setRefreshKey((k) => k + 1)} />
          <StarlinkPanel />
        </div>
        <Gallery refreshKey={refreshKey} />
      </main>
      <footer className="px-4 py-2 border-t border-border text-xs text-muted">
        Planet Hack · world events as 3D digital infiltration · Grok / xAI Imagine
      </footer>
    </div>
  );
}
