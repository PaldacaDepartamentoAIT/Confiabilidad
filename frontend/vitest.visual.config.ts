import { defineConfig } from "vitest/config";

// Pruebas que abren el catálogo en un Chromium real (RF-028 y RF-029). Van aparte de `pnpm test`
// porque necesitan un navegador y son más lentas: `pnpm --filter frontend test:visual`.
export default defineConfig({
  test: {
    environment: "node",
    globals: true,
    include: ["visual/**/*.visual.test.ts"],
    testTimeout: 60_000,
    hookTimeout: 60_000,
  },
});
