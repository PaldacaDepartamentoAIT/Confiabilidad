import type { Page } from "playwright";

// Propiedades de RF-028 que se comparan con igualdad exacta, sin tolerancia.
export const PROPS = [
  "fontSize",
  "fontWeight",
  "fontFamily",
  "lineHeight",
  "letterSpacing",
  "color",
  "backgroundColor",
  "borderTopWidth",
  "borderTopColor",
  "borderBottomWidth",
  "borderBottomColor",
  "borderLeftWidth",
  "borderTopLeftRadius",
  "paddingTop",
  "paddingRight",
  "paddingBottom",
  "paddingLeft",
] as const;

// Alto de las piezas cuyo ancho depende del texto; ancho y alto de las de tamaño fijo.
export const HEIGHT_ONLY = [
  "nav-item",
  "nav-item-active",
  "sidebar-button",
  "topbar",
  "tab",
  "tab-active",
  "search",
  "button-primary",
  "button-secondary",
];
export const FIXED = ["sidebar-header", "menu-toggle", "avatar"];

export type Measures = Record<string, Record<string, string | number>>;

export const VIEWPORT = { width: 1280, height: 900 };

// Estilos calculados de la primera aparición visible de cada pieza marcada con `data-ui`.
export async function measure(page: Page): Promise<Measures> {
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(700);
  return page.evaluate(
    ({ props, fixed, heightOnly }) => {
      const out: Record<string, Record<string, string | number>> = {};
      document.querySelectorAll("[data-ui]").forEach((element) => {
        const key = element.getAttribute("data-ui") as string;
        if (out[key]) return;
        const style = getComputedStyle(element) as unknown as Record<string, string>;
        const box = element.getBoundingClientRect();
        if (box.width === 0 || box.height === 0) return;
        const values: Record<string, string | number> = {};
        props.forEach((prop) => (values[prop] = style[prop]));
        if (fixed.includes(key)) values.width = Math.round(box.width * 10) / 10;
        if (fixed.includes(key) || heightOnly.includes(key)) {
          values.height = Math.round(box.height * 10) / 10;
        }
        out[key] = values;
      });
      return out;
    },
    { props: [...PROPS], fixed: FIXED, heightOnly: HEIGHT_ONLY },
  );
}

// Diferencias entre la referencia y la candidata; las piezas que no están en la candidata se omiten.
export function differences(reference: Measures, candidate: Measures): string[] {
  const found: string[] = [];
  for (const [key, values] of Object.entries(reference)) {
    const other = candidate[key];
    if (!other) continue;
    for (const [prop, value] of Object.entries(values)) {
      if (value !== other[prop]) {
        found.push(`${key}.${prop}: referencia=${value} candidata=${other[prop]}`);
      }
    }
  }
  return found;
}
