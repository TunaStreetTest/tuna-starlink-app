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
    accent: "bg-accent text-bg hover:opacity-90",
    danger: "bg-bad text-bg hover:opacity-80",
    ghost: "bg-transparent border border-border text-text hover:bg-panel",
  };
  return (
    <button
      className={cn(
        "px-3 py-1.5 rounded text-sm transition disabled:opacity-50 disabled:cursor-not-allowed",
        styles[variant],
        className
      )}
      {...props}
    />
  );
}
