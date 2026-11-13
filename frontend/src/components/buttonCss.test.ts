import raw from "./Button.css?raw";

const css = raw.replace(/\/\*[\s\S]*?\*\//g, "");

// El navegador real mide el resultado en `visual/registration.visual.test.ts`; aquí se fijan las reglas para que
// un cambio en ellas falle al momento, sin abrir un navegador.
function declarations(selector: string): string {
  const blocks = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)];
  const found = blocks.find(([, selectors]) =>
    selectors.split(",").some((part) => part.replace(/\s+/g, " ").trim() === selector),
  );
  expect(found, `falta la regla ${selector}`).toBeDefined();
  return found![2];
}

const ENABLED = ':not(:disabled):not([aria-disabled="true"])';

describe("aspecto de botón desactivado", () => {
  it.each([".btn:disabled", '.btn[aria-disabled="true"]'])(
    "%s se ve atenuado al 60 % y con el cursor de no permitido",
    (selector) => {
      const rule = declarations(selector);
      expect(rule).toMatch(/opacity:\s*0\.6/);
      expect(rule).toMatch(/cursor:\s*not-allowed/);
    },
  );

  it("las dos formas de bloquear comparten la misma regla", () => {
    const blocks = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)];
    const shared = blocks.find(([, selectors]) => selectors.includes(".btn:disabled"));
    expect(shared?.[1]).toContain('.btn[aria-disabled="true"]');
  });

  it("el hover del botón principal solo vale para un botón que no está bloqueado", () => {
    expect(declarations(`.btn-primary${ENABLED}:hover`)).toMatch(/background:/);
    expect(css).not.toMatch(/\.btn-primary:hover/);
  });

  it("el hover del botón secundario solo vale para un botón que no está bloqueado", () => {
    expect(declarations(`.btn-ghost.hov${ENABLED}:hover`)).toMatch(/background:/);
    expect(css).not.toMatch(/\.btn-ghost\.hov:hover/);
  });

  it.each([".btn-ghost.hov:disabled:hover", '.btn-ghost.hov[aria-disabled="true"]:hover'])(
    "%s mantiene el fondo transparente aunque otra regla de hover llegue después",
    (selector) => {
      expect(declarations(selector)).toMatch(/background:\s*transparent/);
    },
  );
});
