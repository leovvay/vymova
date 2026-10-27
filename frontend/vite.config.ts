import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

const backend = process.env.VYMOVA_API ?? "http://127.0.0.1:8766";

export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: fileURLToPath(new URL("../backend/vymova/static", import.meta.url)),
    emptyOutDir: true,
    assetsInlineLimit: 0,
  },
  server: {
    port: 5178,
    strictPort: true,
    proxy: { "/api": { target: backend, changeOrigin: true } },
  },
});
