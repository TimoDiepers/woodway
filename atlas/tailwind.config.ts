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
