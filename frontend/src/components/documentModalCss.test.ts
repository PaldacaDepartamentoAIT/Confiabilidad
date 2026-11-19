import css from "./DocumentModal.css?raw";

// El navegador real mide el resultado en `visual/document-modal.visual.test.ts`; aquí se fijan las reglas de
// la guía para que un cambio en ellas falle al momento, sin abrir un navegador.
function rule(source: string, selector: string): string {
  const start = source.indexOf(`${selector} {`);
  expect(start, `falta la regla ${selector}`).toBeGreaterThan(-1);
  return source.slice(start, source.indexOf("}", start));
}

function media(source: string, query: string): string {
  const start = source.indexOf(`@media ${query} {`);
  expect(start, `falta el bloque @media ${query}`).toBeGreaterThan(-1);
  return source.slice(start, source.indexOf("\n}\n", start));
}

describe("aspecto del modal de documento (guía)", () => {
  it("la cortina es negra al 50 %", () => {
    expect(rule(css, ".document-modal::backdrop")).toMatch(
      /background:\s*rgba\(0,\s*0,\s*0,\s*0\.5\)/,
    );
  });

  it("la caja usa el relleno negro del sistema con texto blanco y borde de línea de 1 px", () => {
    const box = rule(css, ".document-box");
    expect(box).toMatch(/background:\s*var\(--black-fill\)/);
    expect(box).toMatch(/color:\s*#ffffff/);
    expect(box).toMatch(/border:\s*1px solid var\(--gray\)/);
  });

  it("mide 640 px como máximo y el 80 % del alto, sin pasar de la pantalla menos 32 px", () => {
    const box = rule(css, ".document-box");
    expect(box).toMatch(/width:\s*640px/);
    expect(box).toMatch(/max-height:\s*min\(80dvh,\s*calc\(100dvh - 32px\)\)/);
  });

  it("por debajo de 700 px ocupa el ancho completo menos 32 px", () => {
    expect(media(css, "(max-width: 699px)")).toMatch(
      /\.document-box\s*\{[^}]*width:\s*calc\(100% - 32px\)/,
    );
  });

  it("solo se desplaza el contenido: la «x» y el pie no se encogen", () => {
    expect(rule(css, ".document-body")).toMatch(/overflow-y:\s*auto/);
    expect(rule(css, ".document-head")).toMatch(/flex:\s*none/);
    expect(rule(css, ".document-foot")).toMatch(/flex:\s*none/);
  });

  it("la página de detrás no se desplaza mientras el modal está abierto", () => {
    expect(rule(css, "body:has(dialog.document-modal[open])")).toMatch(/overflow:\s*hidden/);
  });

  it("aparece con un fundido de 0,2 s", () => {
    expect(rule(css, ".document-modal[open] .document-box")).toMatch(
      /animation:\s*document-in 0\.2s/,
    );
    expect(css).toMatch(/@keyframes document-in/);
  });

  it("los enlaces del documento son azul grisáceo y sin subrayado", () => {
    const link = rule(css, ".document-body a");
    expect(link).toMatch(/color:\s*#7f94b5/);
    expect(link).toMatch(/text-decoration:\s*none/);
  });

  it("la etiqueta de la casilla del pie se lee en blanco", () => {
    expect(rule(css, ".document-box .check")).toMatch(/color:\s*#ffffff/);
  });
});
