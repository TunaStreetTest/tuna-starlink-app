import { useEffect, useState } from "react";

function useMatch(query: string): boolean {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);

  useEffect(() => {
    const mq = window.matchMedia(query);
    const onChange = () => setMatches(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [query]);

  return matches;
}

export function useNarrow(): boolean {
  return useMatch("(max-width: 720px)");
}

/** Phone, a short window, or the X in-app browser. The post stays behind CC. */
export function useCompact(): boolean {
  return useMatch("(max-width: 720px), (max-height: 640px)");
}

export function useReducedMotion(): boolean {
  return useMatch("(prefers-reduced-motion: reduce)");
}
