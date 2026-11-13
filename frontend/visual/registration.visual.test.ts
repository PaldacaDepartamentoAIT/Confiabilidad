import { chromium, type Browser, type Page } from "playwright";

import { startApp, type RunningApp } from "./app";
import { VIEWPORT } from "./measure";

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

type Status = { resend_in: number; resends_left: number };

async function openVerify(scheme: "light" | "dark", viewport = VIEWPORT, status: Status) {
  const context = await browser.newContext({ viewport, colorScheme: scheme });
  const page = await context.newPage();
  const state = { resent: false };
  await page.route(
    (url) => /registration\//.test(url.pathname) && !url.pathname.startsWith("/src"),
    async (route) => {
      const path = new URL(route.request().url()).pathname;
      const json = (body: unknown, code = 200) =>
        route.fulfill({
          status: code,
          contentType: "application/json",
          body: JSON.stringify(body),
        });
      if (path.endsWith("/status")) {
        return json({
          code_expires_in: 600,
          resend_in: state.resent ? 30 : status.resend_in,
          resends_left: state.resent ? status.resends_left - 1 : status.resends_left,
          locked: false,
          expired: false,
        });
      }
      if (path.endsWith("/resend")) {
        state.resent = true;
        return json({ result: "resent" }, 202);
      }
      return json({ countries: [], terms: null, marketing: null });
    },
  );
  await page.goto(`${app.url}register/continue#abc`);
  await page.getByRole("button", { name: "Verify" }).waitFor();
  await page.waitForTimeout(400);
  return { page, context };
}

const box = (page: Page, name: string) =>
  page.getByRole("button", { name }).evaluate((element) => {
    const { x, y, width, height } = element.getBoundingClientRect();
    return { x, y, width, height, right: x + width };
  });

const cardHeight = (page: Page) =>
  page.evaluate(() => document.querySelector(".public-card")!.getBoundingClientRect().height);

describe.each(["light", "dark"] as const)("la verificación en tema %s", (scheme) => {
  const open = { resend_in: 0, resends_left: 3 };

  test("los dos botones van en la misma fila, el secundario a la izquierda y 10 px entre ellos", async () => {
    const { page, context } = await openVerify(scheme, VIEWPORT, open);
    const resend = await box(page, "Send another code");
    const verify = await box(page, "Verify");
    expect(resend.y).toBe(verify.y);
    expect(resend.x).toBeLessThan(verify.x);
    expect(Math.round(verify.x - resend.right)).toBe(10);
    const form = await page.locator(".form-actions").evaluate((element) => {
      const { right } = element.getBoundingClientRect();
      return right;
    });
    expect(Math.round(form - verify.right)).toBe(0);
    await context.close();
  });

  test("a 420 px quedan en dos filas a todo el ancho con «Verificar» arriba", async () => {
    const { page, context } = await openVerify(scheme, { width: 420, height: 900 }, open);
    const resend = await box(page, "Send another code");
    const verify = await box(page, "Verify");
    expect(verify.y).toBeLessThan(resend.y);
    expect(Math.round(verify.width)).toBe(Math.round(resend.width));
    expect(Math.round(verify.x)).toBe(Math.round(resend.x));
    const row = await page
      .locator(".form-actions")
      .evaluate((e) => e.getBoundingClientRect().width);
    expect(Math.round(verify.width)).toBe(Math.round(row));
    await context.close();
  });

  test("a 480 px todavía caben en una fila", async () => {
    const { page, context } = await openVerify(scheme, { width: 480, height: 900 }, open);
    const resend = await box(page, "Send another code");
    const verify = await box(page, "Verify");
    expect(resend.y).toBe(verify.y);
    await context.close();
  });

  test("un botón bloqueado se ve atenuado, con cursor de no permitido y sin hover", async () => {
    const { page, context } = await openVerify(scheme, VIEWPORT, {
      resend_in: 45,
      resends_left: 3,
    });
    const resend = page.getByRole("button", { name: /Send another code in/ });
    expect(await resend.isDisabled()).toBe(true);
    const read = () =>
      resend.evaluate((element) => {
        const style = getComputedStyle(element);
        return {
          opacity: style.opacity,
          cursor: style.cursor,
          background: style.backgroundColor,
          color: style.color,
          border: style.borderTopColor,
        };
      });
    const resting = await read();
    expect(resting.opacity).toBe("0.6");
    expect(resting.cursor).toBe("not-allowed");
    await resend.hover({ force: true });
    await page.waitForTimeout(500);
    expect(await read()).toEqual(resting);
    await context.close();
  });

  test("un botón activo sí cambia de color al pasar el puntero", async () => {
    const { page, context } = await openVerify(scheme, VIEWPORT, open);
    const verify = page.getByRole("button", { name: "Verify" });
    const background = () =>
      verify.evaluate((element) => getComputedStyle(element).backgroundColor);
    const resting = await background();
    await verify.hover();
    await page.waitForTimeout(500);
    expect(await background()).not.toBe(resting);
    expect(await verify.evaluate((element) => getComputedStyle(element).opacity)).toBe("1");
    await context.close();
  });

  test.each([
    ["1280", VIEWPORT],
    ["420", { width: 420, height: 900 }],
  ])("la card mide lo mismo con y sin mensaje de reenvío (%s px)", async (_label, viewport) => {
    const { page, context } = await openVerify(scheme, viewport, open);
    const slot = page.locator(".resend-slot");
    expect(await slot.evaluate((element) => element.textContent)).toBe("");
    const before = await cardHeight(page);
    await page.getByRole("button", { name: "Send another code" }).click();
    await page.getByText("you will receive a new code").waitFor();
    expect(await cardHeight(page)).toBe(before);
    await context.close();
  });

  test("el hueco mide dos líneas y está debajo del recuento de códigos", async () => {
    const { page, context } = await openVerify(scheme, VIEWPORT, open);
    const geometry = await page.evaluate(() => {
      const slot = document.querySelector(".resend-slot") as HTMLElement;
      const count = document.querySelector(".resend-count") as HTMLElement;
      const fontSize = parseFloat(getComputedStyle(slot).fontSize);
      return {
        slot: slot.getBoundingClientRect(),
        countBottom: count.getBoundingClientRect().bottom,
        twoLines: 2 * 1.45 * fontSize,
      };
    });
    expect(geometry.slot.height).toBeGreaterThanOrEqual(Math.floor(geometry.twoLines));
    expect(geometry.slot.top).toBeGreaterThanOrEqual(Math.floor(geometry.countBottom));
    await context.close();
  });
});
