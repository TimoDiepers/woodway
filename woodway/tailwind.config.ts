import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        paper: "rgb(var(--color-paper) / <alpha-value>)",
        panel: "rgb(var(--color-panel) / <alpha-value>)",
        panelBorder: "rgb(var(--color-panel-border) / <alpha-value>)",
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        inkMuted: "rgb(var(--color-ink-muted) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        moss: "#3d552d",
        mossSoft: "#a9bc8f",
        clay: "#6e3d3a",
        fjord: "#1e536d",
        dac: "#9a6516",
        dacSoft: "#e8cb92",
        co2: "#2e7d4f",
        alb: "#c8641a",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        serif: ["Literata", "Georgia", "serif"],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
