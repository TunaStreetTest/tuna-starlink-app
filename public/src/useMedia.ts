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

export function useReducedMotion(): boolean {
  return useMatch("(prefers-reduced-motion: reduce)");
}
