import tokens from "./tokens.css?raw";

// Tablas «Tema claro» y «Tema oscuro» de docs/identidad-visual.md. El relleno fuerte es la tinta
// en el tema claro, y el texto sobre el color de acción es blanco en claro y el lienzo en oscuro.
const LIGHT = {
  canvas: "#dbe5eb",
  block: "#ffffff",
  support: "#edf3f7",
  line: "#d1dde5",
  "line-strong": "#768c9b",
  "text-secondary": "#384d5c",
  ink: "#0f222e",
  "fill-strong": "#0f222e",
  action: "#1b5983",
  "on-action": "#ffffff",
  "accent-1": "#6aafdc",
  "accent-2": "#c9e2f2",
  "alarm-p1": "#8a2f3a",
  "alarm-p2": "#80442b",
  warning: "#655423",
};

const DARK = {
  canvas: "#0c161d",
  block: "#162631",
  support: "#1f313d",
  line: "#293e4c",
  "line-strong": "#627d90",
  "text-secondary": "#b3c5d0",
  ink: "#eaf1f6",
  "fill-strong": "#344855",
  action: "#9cc9e8",
  "on-action": "#0c161d",
  "accent-1": "#4f95c4",
  "accent-2": "#9cc9e8",
  "alarm-p1": "#d97f87",
  "alarm-p2": "#d29a76",
  warning: "#c4b07a",
};

function variables(block: string): Record<string, string> {
  return Object.fromEntries(
    [...block.matchAll(/--color-([a-z0-9-]+):\s*(#[0-9a-f]{6});/g)].map(([, name, value]) => [
      name,
      value,
    ]),
  );
}

// Devuelve las declaraciones de la primera regla cuyo selector es exactamente `selector`.
function rule(css: string, selector: string): string {
  const start = css.indexOf(`${selector} {`);
  expect(start).toBeGreaterThan(-1);
  return css.slice(start, css.indexOf("}", start));
}

describe("identidad visual", () => {
  it("define la paleta del tema claro", () => {
    const light = tokens.slice(0, tokens.indexOf("@media"));
    expect(variables(light)).toEqual(LIGHT);
  });

  it("aplica la paleta oscura con el sistema en oscuro, salvo si se eligió el claro", () => {
    const media = tokens.slice(tokens.indexOf("@media (prefers-color-scheme: dark)"));
    const system = rule(media, ':root:not([data-theme="light"])');
    expect(variables(system)).toEqual(DARK);
    expect(system).toContain("color-scheme: dark;");
  });

  it("aplica la paleta oscura cuando se eligió el oscuro", () => {
    const chosen = rule(tokens, ':root[data-theme="dark"]');
    expect(variables(chosen)).toEqual(DARK);
    expect(chosen).toContain("color-scheme: dark;");
  });
});
