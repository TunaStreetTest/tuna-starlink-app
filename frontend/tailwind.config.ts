import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#070812",
        panel: "#0c1218",
        border: "#1c3c46",
        muted: "#8ea0aa",
        text: "#f4f1ea",
        accent: "#7ef0ff",
        hot: "#ff9ad6",
        acid: "#c6f54e",
        gold: "#f5c842",
        warn: "#f5c842",
        bad: "#ff6b7a",
        ok: "#9dff6a",
      },
      fontFamily: {
        serif: ['"Iowan Old Style"', "Palatino", "Georgia", "serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
