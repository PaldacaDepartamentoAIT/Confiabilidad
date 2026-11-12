import tokens from "./tokens.css?raw";
import base from "./base.css?raw";

// Tablas «Tema claro», «Tema oscuro» y «Estados de alarma» de docs/identidad-visual.md.
const LIGHT = {
  bg: "#f8f9f9",
  ink: "#1b1e22",
  text2: "#61656b",
  gray: "#c3c5c7",
  grid: "#d8dadb",
  ctrl: "#8d9094",
  primary: "#546c8c",
  "on-primary": "#ffffff",
  secondary: "#d8dbdf",
  "menu-btn-bg": "#1b1e22",
  "menu-btn-icon": "#d8dbdf",
  "black-fill": "#1b1e22",
  p1: "#a47070",
  p2: "#915535",
  warn: "#7a7020",
};

const DARK = {
  bg: "#111213",
  ink: "#eeeff1",
  text2: "#aaadb0",
  gray: "#47484a",
  grid: "#313234",
  ctrl: "#5f6163",
  primary: "#9fafc6",
  "on-primary": "#111213",
  secondary: "#535a65",
  "menu-btn-bg": "#ffffff",
  "menu-btn-icon": "#535a65",
  "black-fill": "#000000",
  p1: "#a47070",
  p2: "#d9977a",
  warn: "#c9bd8c",
};

function variables(block: string): Record<string, string> {
  return Object.fromEntries(
    [...block.matchAll(/--([a-z0-9-]+):\s*(#[0-9a-f]{6});/g)].map(([, name, value]) => [
      name,
      value,
    ]),
  );
}

const MEDIA = "@media (prefers-color-scheme: dark)";
const FORCED_DARK = ':root[data-theme="dark"]';

function lightBlock(css: string): string {
  return css.slice(0, css.indexOf(MEDIA));
}

function mediaBlock(css: string): string {
  const start = css.indexOf(MEDIA);
  expect(start).toBeGreaterThan(-1);
  return css.slice(start, css.indexOf(FORCED_DARK));
}

function forcedDarkBlock(css: string): string {
  const start = css.indexOf(FORCED_DARK);
  expect(start).toBeGreaterThan(-1);
  return css.slice(start, css.indexOf("}", start));
}

describe("identidad visual: paleta Pizarra", () => {
  it("define la paleta del tema claro", () => {
    expect(variables(lightBlock(tokens))).toEqual(LIGHT);
  });

  it("define la paleta oscura según el sistema operativo salvo que se fije el tema claro", () => {
    const block = mediaBlock(tokens);
    expect(block).toContain(':root:not([data-theme="light"])');
    expect(variables(block)).toEqual(DARK);
  });

  it("define la paleta oscura cuando se fija el tema oscuro", () => {
    expect(variables(forcedDarkBlock(tokens))).toEqual(DARK);
  });

  it("declara el esquema de color de cada tema", () => {
    expect(lightBlock(tokens)).toContain("color-scheme: light");
    expect(mediaBlock(tokens)).toContain("color-scheme: dark");
    expect(forcedDarkBlock(tokens)).toContain("color-scheme: dark");
  });

  it("ya no contiene la paleta Niebla marina", () => {
    expect(tokens).not.toMatch(/--color-/);
    expect(base).not.toMatch(/--color-/);
  });

  it("define las fuentes del proyecto", () => {
    expect(tokens).toMatch(/--font:\s*"Manrope Variable"/);
    expect(tokens).toMatch(/--mono:\s*"JetBrains Mono Variable"/);
  });
});

describe("identidad visual: reglas generales", () => {
  it("quita todas las animaciones y transiciones con movimiento reducido", () => {
    const start = base.indexOf("@media (prefers-reduced-motion: reduce)");
    expect(start).toBeGreaterThan(-1);
    const block = base.slice(start);
    expect(block).toMatch(/transition:\s*none\s*!important/);
    expect(block).toMatch(/animation:\s*none\s*!important/);
  });

  it("muestra el foco con 2 px en el color principal separado 2 px", () => {
    expect(base).toMatch(/:focus-visible\s*\{[^}]*outline:\s*2px solid var\(--primary\)/);
    expect(base).toMatch(/:focus-visible\s*\{[^}]*outline-offset:\s*2px/);
  });

  it("usa la tinta sobre el fondo y Manrope a 14 px en el cuerpo", () => {
    expect(base).toMatch(/body\s*\{[^}]*background:\s*var\(--bg\)/);
    expect(base).toMatch(/body\s*\{[^}]*color:\s*var\(--ink\)/);
    expect(base).toMatch(/body\s*\{[^}]*font:\s*400 14px\/1\.45 var\(--font\)/);
  });

  it("no estila elementos sueltos: solo reinicia la fuente, el color y el cursor de los controles", () => {
    const rules = [...base.matchAll(/([^{}@]+)\{([^{}]*)\}/g)].map(([, selector, body]) => ({
      selectors: selector.split(",").map((part) => part.trim()),
      properties: body
        .split(";")
        .map((declaration) => declaration.split(":")[0].trim())
        .filter(Boolean),
    }));
    const loose = /^(button|input|select|textarea|main|form|section)$/;

    for (const { selectors, properties } of rules) {
      if (!selectors.some((selector) => loose.test(selector))) continue;
      expect(selectors.every((selector) => /^(button|input|select|textarea)$/.test(selector))).toBe(
        true,
      );
      properties.forEach((property) => expect(["font", "color", "cursor"]).toContain(property));
    }
    expect(rules.some(({ selectors }) => selectors.includes("main"))).toBe(false);
  });
});
