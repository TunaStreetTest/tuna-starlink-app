import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

type Variant = "default" | "danger" | "ghost" | "accent";

export function Button({
  className,
  variant = "default",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  const styles: Record<Variant, string> = {
    default: "bg-text text-bg hover:opacity-80",
    accent:
      "border border-accent/70 bg-accent/10 text-[#d8fbff] tracking-[0.16em] uppercase hover:bg-accent/20",
    danger: "border border-bad/70 bg-bad/10 text-bad tracking-[0.14em] uppercase hover:bg-bad/20",
    ghost:
      "bg-transparent border border-accent/30 text-[#d8fbff] tracking-[0.12em] uppercase hover:border-accent/70",
  };
  return (
    <button
      className={cn(
        "px-3 py-1.5 rounded-full text-xs transition disabled:opacity-50 disabled:cursor-not-allowed",
        styles[variant],
        className
      )}
      {...props}
    />
  );
}
