import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const root = dirname(fileURLToPath(import.meta.url)); // Windows-safe absolute path

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": root } },
  test: {
    environment: "jsdom",
    css: false,
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
  },
});
