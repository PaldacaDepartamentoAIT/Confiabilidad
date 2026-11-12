import { createServer } from "vite";

export type RunningApp = { url: string; close: () => Promise<void> };

// Levanta el servidor de desarrollo de Vite en un puerto libre, para que las pruebas visuales abran la
// aplicación real sin depender de que haya una ya en marcha.
export async function startApp(): Promise<RunningApp> {
  const server = await createServer({
    configFile: "vite.config.ts",
    logLevel: "error",
    server: { port: 0, strictPort: false, hmr: false },
  });
  await server.listen();
  const url = server.resolvedUrls?.local[0];
  if (!url) throw new Error("Vite did not report its address");
  return { url, close: () => server.close() };
}
