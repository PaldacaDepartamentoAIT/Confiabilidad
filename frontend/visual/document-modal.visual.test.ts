import { chromium, type Browser, type Page } from "playwright";

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

const OPEN = "Abrir el documento";
const DIALOG = "dialog.document-modal[open]";

async function openPage(scheme: "light" | "dark", viewport = VIEWPORT) {
  const context = await browser.newContext({ viewport, colorScheme: scheme });
  const page = await context.newPage();
  await page.goto(app.url);
  await page.getByRole("region", { name: "Documento en un modal" }).waitFor();
  return { page, context };
}

async function openModal(page: Page) {
  const button = page.getByRole("button", { name: OPEN });
  await button.scrollIntoViewIfNeeded();
  await button.click();
  await page.locator(DIALOG).waitFor();
  await page.waitForTimeout(300);
}

const boxSize = (page: Page) =>
  page.evaluate(() => {
    const box = document.querySelector(".document-box") as HTMLElement;
    const { width, height } = box.getBoundingClientRect();
    return { width: Math.round(width), height: Math.round(height) };
  });

describe.each(["light", "dark"] as const)("el modal de documento en tema %s", (scheme) => {
  test("la cortina es negra al 50 % y la caja usa el relleno negro de la guía", async () => {
    const { page, context } = await openPage(scheme);
    await openModal(page);

    const styles = await page.evaluate(() => {
      const dialog = document.querySelector("dialog.document-modal") as HTMLElement;
      const box = dialog.querySelector(".document-box") as HTMLElement;
      const boxStyle = getComputedStyle(box);
      return {
        curtain: getComputedStyle(dialog, "::backdrop").backgroundColor,
        background: boxStyle.backgroundColor,
        color: boxStyle.color,
        border: boxStyle.borderTopWidth,
        borderColor: boxStyle.borderTopColor,
        radius: boxStyle.borderTopLeftRadius,
        link: getComputedStyle(box.querySelector(".document-body a") as HTMLElement),
      };
    });

    expect(styles.curtain).toBe("rgba(0, 0, 0, 0.5)");
    expect(styles.background).toBe(scheme === "light" ? "rgb(27, 30, 34)" : "rgb(0, 0, 0)");
    expect(styles.color).toBe("rgb(255, 255, 255)");
    expect(styles.border).toBe("1px");
    expect(styles.radius).toBe("4px");
    await context.close();
  });

  test("los enlaces del documento son azul grisáceo, sin subrayado y se abren en pestaña nueva", async () => {
    const { page, context } = await openPage(scheme);
    await openModal(page);

    const link = page.locator(".document-body a");
    expect(await link.evaluate((a) => getComputedStyle(a).color)).toBe("rgb(127, 148, 181)");
    expect(await link.evaluate((a) => getComputedStyle(a).textDecorationLine)).toBe("none");
    expect(await link.getAttribute("target")).toBe("_blank");
    await context.close();
  });

  test("Tab y Mayús+Tab no llevan el foco a la página de detrás", async () => {
    const { page, context } = await openPage(scheme);
    await openModal(page);

    // Al salir del último elemento, el navegador puede llevar el foco a su propia interfaz (entonces no hay
    // elemento activo en la página); lo que no puede pasar es que caiga en un elemento de la página.
    for (const key of [
      "Tab",
      "Tab",
      "Tab",
      "Tab",
      "Tab",
      "Tab",
      "Shift+Tab",
      "Shift+Tab",
      "Shift+Tab",
    ]) {
      await page.keyboard.press(key);
      const onPage = await page.evaluate(() => {
        const active = document.activeElement;
        return active !== document.body && !document.querySelector("dialog")?.contains(active);
      });
      expect(onPage).toBe(false);
    }
    await context.close();
  });

  test("la página de detrás no se desplaza mientras está abierto", async () => {
    const { page, context } = await openPage(scheme);
    await openModal(page);
    const before = await page.evaluate(() => window.scrollY);

    await page.mouse.move(5, 5);
    await page.mouse.wheel(0, 600);
    await page.waitForTimeout(200);

    expect(await page.evaluate(() => window.scrollY)).toBe(before);
    expect(await page.evaluate(() => getComputedStyle(document.body).overflow)).toBe("hidden");
    await context.close();
  });

  test.each([
    ["la «x»", (page: Page) => page.getByRole("button", { name: "Close" }).click()],
    ["la tecla Escape", (page: Page) => page.keyboard.press("Escape")],
    ["un clic en la cortina", (page: Page) => page.mouse.click(5, 5)],
  ])("se cierra con %s y el foco vuelve al botón que lo abrió", async (_name, close) => {
    const { page, context } = await openPage(scheme);
    await openModal(page);

    await close(page);
    await page.waitForTimeout(200);

    expect(await page.locator("dialog").count()).toBe(0);
    expect(await page.evaluate(() => document.activeElement?.textContent)).toBe(OPEN);
    expect(await page.evaluate(() => getComputedStyle(document.body).overflow)).not.toBe("hidden");
    await context.close();
  });

  test("mide 640 px de ancho y como mucho el 80 % del alto", async () => {
    const { page, context } = await openPage(scheme);
    await openModal(page);

    const size = await boxSize(page);

    expect(size.width).toBe(640);
    expect(size.height).toBeLessThanOrEqual(0.8 * VIEWPORT.height);
    await context.close();
  });

  test("por debajo de 700 px ocupa el ancho completo menos 32 px", async () => {
    const { page, context } = await openPage(scheme, { width: 600, height: 800 });
    await openModal(page);

    expect((await boxSize(page)).width).toBe(568);
    await context.close();
  });

  test("con el modal abierto, al cambiar el tamaño de la ventana se recalcula", async () => {
    const { page, context } = await openPage(scheme);
    await openModal(page);
    expect((await boxSize(page)).width).toBe(640);

    await page.setViewportSize({ width: 420, height: 700 });
    await page.waitForTimeout(200);

    expect((await boxSize(page)).width).toBe(388);
    expect(await page.locator(DIALOG).count()).toBe(1);
    await context.close();
  });

  test("con muy poco alto deja 16 px arriba y abajo y la «x» y la casilla siguen a la vista", async () => {
    const { page, context } = await openPage(scheme, { width: 900, height: 120 });
    await openModal(page);

    const size = await boxSize(page);
    expect(size.height).toBeLessThanOrEqual(120 - 32);
    const dialog = page.locator(DIALOG);
    for (const target of [
      dialog.getByRole("button", { name: "Close" }),
      dialog.getByRole("checkbox", { name: "Acepto los términos" }),
    ]) {
      const box = await target.boundingBox();
      expect(box).not.toBeNull();
      expect(box!.y).toBeGreaterThanOrEqual(0);
      expect(box!.y + box!.height).toBeLessThanOrEqual(120);
    }
    await context.close();
  });

  test("solo se desplaza el contenido, no la «x» ni el pie", async () => {
    const { page, context } = await openPage(scheme, { width: 900, height: 400 });
    await openModal(page);
    const close = page.getByRole("button", { name: "Close" });
    const before = await close.boundingBox();

    await page.locator(".document-body").evaluate((element) => (element.scrollTop = 200));
    await page.waitForTimeout(100);

    expect(
      await page.locator(".document-body").evaluate((element) => element.scrollTop),
    ).toBeGreaterThan(0);
    expect(await close.boundingBox()).toEqual(before);
    await context.close();
  });

  test("abierto no tiene violaciones de contraste AA ni de accesibilidad", async () => {
    const { page, context } = await openPage(scheme);
    await openModal(page);

    expect(await accessibilityViolations(page)).toEqual([]);
    await context.close();
  });
});
