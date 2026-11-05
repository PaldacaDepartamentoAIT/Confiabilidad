/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    // La web habla con la API en su mismo origen (D-10); en desarrollo, Vite la reenvía al backend.
    // Se conserva el Host del navegador: Django lo compara con el Origin de cada POST (CSRF).
    proxy: {
      "/api": {
        target: loadEnv(mode, ".").VITE_BACKEND_URL ?? "http://localhost:8000",
        changeOrigin: false,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.ts",
    // El test de la paleta lee el CSS; los demás estilos no se procesan en los tests.
    css: { include: [/src\/styles\/tokens\.css/] },
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx", "src/setupTests.ts", "src/vite-env.d.ts"],
      thresholds: {
        lines: 80,
      },
    },
  },
}));
