import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

// base "./" so the built app works under /dissvortrag/atlas/ on Pages and from any folder.
export default defineConfig({
  base: "./",
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  test: { globals: true, environment: "jsdom", setupFiles: ["./tests/setup.ts"], css: true },
});
