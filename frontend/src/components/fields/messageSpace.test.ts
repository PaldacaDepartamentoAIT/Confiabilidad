import checkbox from "./Checkbox.css?raw";
import field from "./field.css?raw";

// El navegador real mide que el error no mueve nada; aquí se fija la regla que lo consigue: una línea
// de 16 px reservada bajo cada campo, que el error ocupa cuando aparece.
function rule(css: string, selector: string): string {
  const start = css.indexOf(`${selector} {`);
  expect(start, `falta la regla ${selector}`).toBeGreaterThan(-1);
  return css.slice(start, css.indexOf("}", start));
}

describe("reserva del mensaje de error", () => {
  it("el campo reserva 20 px bajo su caja", () => {
    const reserve = rule(field, ".fld::after");
    expect(reserve).toMatch(/content:\s*""/);
    expect(reserve).toMatch(/height:\s*20px/);
  });

  it("el hueco de 8 px y el margen de -6 px dejan el error a 2 px de la caja", () => {
    const container = rule(field, ".fld");
    expect(container).toMatch(/--msg-offset:\s*-6px/);
    expect(container).toMatch(/gap:\s*8px/);
    expect(container).not.toMatch(/margin-bottom/);
  });

  it("el error ocupa la línea reservada y no la suma a ella", () => {
    expect(rule(field, ".fld:has(> .error-msg)::after")).toMatch(/content:\s*none/);
    const message = rule(field, ".error-msg");
    expect(message).toMatch(/min-height:\s*20px/);
    expect(message).toMatch(/line-height:\s*16px/);
  });

  it("el margen del error gana al de los párrafos de un bloque", () => {
    expect(field).toMatch(
      /\.fld > \.error-msg,\s*\.check-field > \.error-msg\s*\{[^}]*margin-top:\s*var\(--msg-offset/,
    );
  });

  it("la casilla reserva la misma línea y la oculta con el error", () => {
    expect(rule(checkbox, ".check-field::after")).toMatch(/height:\s*20px/);
    expect(rule(checkbox, ".check-field:has(> .error-msg)::after")).toMatch(/content:\s*none/);
  });
});
