import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";
import fs from "node:fs";

// Dev only: serve the built HTML deck (../deck/dist) under /deck/ so the talk can embed it in an iframe.
const deckDist = path.resolve(__dirname, "../deck/dist");
const serveDeck = {
  name: "serve-deck",
  configureServer(server: import("vite").ViteDevServer) {
    server.middlewares.use("/deck", (req, res, next) => {
      const p = path.join(deckDist, decodeURIComponent((req.url ?? "/").split("?")[0]).replace(/^\/$/, "/index.html"));
      if (!p.startsWith(deckDist) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) return next();
      res.setHeader("Content-Type", p.endsWith(".html") ? "text/html" : p.endsWith(".js") ? "text/javascript" : p.endsWith(".css") ? "text/css" : "application/octet-stream");
      fs.createReadStream(p).pipe(res);
    });
  },
};

// base "./" so the built app works under /dissvortrag/atlas/ on Pages and from any folder.
export default defineConfig({
  base: "./",
  plugins: [react(), serveDeck],
  server: { fs: { allow: [".."] } },
  build: { rollupOptions: { input: { main: path.resolve(__dirname, "index.html"), talk: path.resolve(__dirname, "talk.html") } } },
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  test: { globals: true, environment: "jsdom", setupFiles: ["./tests/setup.ts"], css: true },
});
