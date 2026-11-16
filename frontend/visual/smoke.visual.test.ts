import { chromium, type Browser } from "playwright";

import { startApp, type RunningApp } from "./app";

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

test.each(["light", "dark"] as const)(
  "el catálogo se abre en Chromium en tema %s",
  async (scheme) => {
    const context = await browser.newContext({
      colorScheme: scheme,
      viewport: { width: 1280, height: 900 },
    });
    const page = await context.newPage();
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));

    await page.goto(app.url);

    await page.getByRole("region", { name: "Indicadores" }).waitFor();
    expect(await page.locator("[data-ui='indicator']").count()).toBeGreaterThan(0);
    expect(await page.locator("html").getAttribute("data-theme")).toBeNull();
    const background = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    expect(background).toBe(scheme === "light" ? "rgb(248, 249, 249)" : "rgb(17, 18, 19)");
    expect(errors).toEqual([]);
    await context.close();
  },
);
