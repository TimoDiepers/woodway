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
      let rel: string;
      try { rel = decodeURIComponent((req.url ?? "/").split("?")[0]); } catch { return next(); }   // malformed %-escapes
      const p = path.join(deckDist, rel.replace(/^\/$/, "/index.html"));
      if (!(p === deckDist || p.startsWith(deckDist + path.sep)) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) return next();
      res.setHeader("Content-Type", p.endsWith(".html") ? "text/html" : p.endsWith(".js") ? "text/javascript" : p.endsWith(".css") ? "text/css" : "application/octet-stream");
      fs.createReadStream(p).pipe(res);
    });
  },
};

// base "./" so the built app works at the site root (woodway.tidi.dev), under /dissvortrag/ on github.io, or from any folder.
export default defineConfig({
  base: "./",
  plugins: [react(), serveDeck],
  server: { fs: { allow: [path.resolve(__dirname, "../deck"), __dirname] } },
  // the React talk (talk.html) is no longer published: the slides are the HTML deck under /slides/
  build: { rollupOptions: { input: { main: path.resolve(__dirname, "index.html") } } },
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  test: { globals: true, environment: "jsdom", setupFiles: ["./tests/setup.ts"], css: true },
});
