import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type Tone = "ok" | "warn" | "bad" | "neutral" | "accent" | "hot";

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  const tones: Record<Tone, string> = {
    ok: "bg-ok/20 text-ok border-ok/40",
    warn: "bg-warn/20 text-warn border-warn/40",
    bad: "bg-bad/20 text-bad border-bad/40",
    accent: "bg-accent/15 text-accent border-accent/40",
    hot: "bg-hot/15 text-hot border-hot/40",
    neutral: "bg-border text-muted border-border",
  };
  return (
    <span className={cn("inline-block px-2 py-0.5 text-[0.68rem] font-mono tracking-[0.12em] uppercase rounded border", tones[tone])}>
      {children}
    </span>
  );
}

export function Dot({ tone = "neutral" }: { tone?: Tone }) {
  const tones: Record<Tone, string> = {
    ok: "bg-ok",
    warn: "bg-warn",
    bad: "bg-bad",
    accent: "bg-accent",
    hot: "bg-hot",
    neutral: "bg-muted",
  };
  return <span className={cn("inline-block w-2 h-2 rounded-full", tones[tone])} />;
}
