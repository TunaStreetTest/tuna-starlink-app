import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0c12",
        panel: "#12151e",
        border: "#1e2433",
        muted: "#7d8799",
        text: "#e8edf5",
        accent: "#5b9fd4",
        hot: "#e84855",
        gold: "#f5c842",
        warn: "#d29922",
        bad: "#f85149",
        ok: "#3fb950",
      },
    },
  },
  plugins: [],
} satisfies Config;
