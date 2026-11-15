import { cn } from "@/lib/utils";
import type { HTMLAttributes, ReactNode } from "react";

export function Card({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "border border-accent/25 bg-panel/80 rounded-md p-4 shadow-[0_0_40px_rgba(0,0,0,0.35)]",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <h2 className={cn("font-mono text-xs tracking-[0.18em] uppercase text-accent mb-3", className)}>
      {children}
    </h2>
  );
}

