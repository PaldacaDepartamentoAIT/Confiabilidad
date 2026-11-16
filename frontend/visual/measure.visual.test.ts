import { differences } from "./measure";

test("no hay diferencias si todo coincide", () => {
  const reference = { block: { fontSize: "14px", color: "rgb(0, 0, 0)" } };
  expect(differences(reference, { block: { fontSize: "14px", color: "rgb(0, 0, 0)" } })).toEqual(
    [],
  );
});

test("cada propiedad distinta es una diferencia, con su pieza y sus dos valores", () => {
  const reference = { block: { fontSize: "14px", color: "rgb(0, 0, 0)" } };
  const candidate = { block: { fontSize: "15px", color: "rgb(0, 0, 0)" } };
  expect(differences(reference, candidate)).toEqual([
    "block.fontSize: referencia=14px candidata=15px",
  ]);
});

test("una propiedad que la candidata no mide cuenta como diferencia", () => {
  expect(differences({ block: { height: 36 } }, { block: {} })).toEqual([
    "block.height: referencia=36 candidata=undefined",
  ]);
});

test("las piezas que no están en la candidata se omiten", () => {
  expect(differences({ chart: { fontSize: "12px" } }, {})).toEqual([]);
});
