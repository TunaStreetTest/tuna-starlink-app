import { useState } from "react";

import { Gallery } from "@/components/Gallery";
import { GeneratePanel } from "@/components/GeneratePanel";
import { HealthBar } from "@/components/HealthBar";
import { StarlinkPanel } from "@/components/StarlinkPanel";

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="relative min-h-full flex flex-col">
      <div className="vignette" />
      <HealthBar />
      <main className="relative z-10 flex-1 px-4 py-6 max-w-[1600px] mx-auto w-full space-y-8">
        <GeneratePanel onStarted={() => setRefreshKey((k) => k + 1)} />
        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_300px] gap-4 items-start">
          <Gallery refreshKey={refreshKey} />
          <StarlinkPanel />
        </div>
      </main>
      <footer className="relative z-10 px-4 py-3 font-mono text-[0.68rem] tracking-[0.18em] uppercase text-muted">
        Planet Hack · tuned to the wire
      </footer>
    </div>
  );
}
