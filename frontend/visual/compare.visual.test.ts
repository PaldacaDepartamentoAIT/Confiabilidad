import { chromium, type Browser } from "playwright";

import { startApp, type RunningApp } from "./app";
import { VIEWPORT, differences, measure } from "./measure";

const REFERENCES = ["crear-empresa.html", "activos.html"];
const referenceUrl = (file: string) =>
  new URL(`../../docs/referencia/${file}`, import.meta.url).href;

let app: RunningApp;
let browser: Browser;

beforeAll(async () => {
  app = await startApp();
  browser = await chromium.launch();
});

afterAll(async () => {
  await browser?.close();
  await app?.close();
});

async function measureUrl(url: string, scheme: "light" | "dark") {
  const context = await browser.newContext({ viewport: VIEWPORT, colorScheme: scheme });
  const page = await context.newPage();
  await page.goto(url);
  const measures = await measure(page);
  await context.close();
  return measures;
}

describe.each(["light", "dark"] as const)(
  "el catálogo coincide con las referencias en tema %s",
  (scheme) => {
    test.each(REFERENCES)("%s", async (file) => {
      const reference = await measureUrl(referenceUrl(file), scheme);
      const catalog = await measureUrl(app.url, scheme);

      // Que no pase en vacío: la mayoría de las piezas de la referencia deben existir en el catálogo.
      const shared = Object.keys(reference).filter((key) => key in catalog);
      expect(shared.length).toBeGreaterThanOrEqual(15);
      expect(differences(reference, catalog)).toEqual([]);
    });
  },
);
