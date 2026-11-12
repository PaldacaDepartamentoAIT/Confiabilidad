import { chromium, type Browser } from "playwright";

import { startApp, type RunningApp } from "./app";
import { VIEWPORT, accessibilityViolations } from "./measure";

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

describe.each(["light", "dark"] as const)("accesibilidad del catálogo en tema %s", (scheme) => {
  test.each([
    ["escritorio", VIEWPORT],
    ["móvil", { width: 420, height: 900 }],
  ])("sin violaciones de contraste AA ni de accesibilidad (%s)", async (_name, viewport) => {
    const context = await browser.newContext({ viewport, colorScheme: scheme });
    const page = await context.newPage();
    await page.goto(app.url);
    await page.getByRole("region", { name: "Indicadores" }).waitFor();

    expect(await accessibilityViolations(page)).toEqual([]);
    await context.close();
  });
});
