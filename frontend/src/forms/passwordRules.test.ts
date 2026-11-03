import type { Validator } from "./useFormValidation";
import { minimumLength, newPasswordRules, notOnlyDigits } from "./passwordRules";

function firstError(value: string) {
  for (const rule of newPasswordRules as Validator[]) {
    const error = rule(value);
    if (error) return error.key;
  }
  return null;
}

test.each([
  ["abcdefghijk", "passwordTooShort"],
  ["🙂🙂🙂🙂🙂🙂", "passwordTooShort"],
  ["123", "passwordTooShort"],
  ["123456789012", "passwordOnlyDigits"],
  ["１２３４５６７８９０１２", "passwordOnlyDigits"],
  ["١٢٣٤٥٦٧٨٩٠١٢", "passwordOnlyDigits"],
])("rejects %j with %s", (value, key) => {
  expect(firstError(value)).toBe(key);
});

test.each(["abcdefghijkl", "12345678901a", "🙂🙂🙂🙂🙂🙂🙂🙂🙂🙂🙂🙂", "correct horse"])(
  "accepts %j",
  (value) => {
    expect(firstError(value)).toBeNull();
  },
);

// Tabla «Casos compartidos de contraseña» de specs/registro-flujo/spec.md (CF-8): el test del
// backend recorre la misma; si cambia una, cambia la otra.
const SHARED_CASES: [string, boolean, boolean][] = [
  ["abcdefghijk", false, false],
  ["abcdefghijkl", true, false],
  ["😀".repeat(11), false, false],
  ["😀".repeat(12), true, false],
  ["123456789012", true, true],
  ["١٢٣٤٥٦٧٨٩٠١٢", true, true],
  ["²".repeat(12), true, true],
  ["12345678901a", true, false],
];

test.each(SHARED_CASES)(
  "shared case %j: at least 12 is %s, only digits is %s",
  (password, longEnough, onlyDigits) => {
    expect(minimumLength(password) === null).toBe(longEnough);
    expect(notOnlyDigits(password) !== null).toBe(onlyDigits);
  },
);

test.each(["⁰¹²³⁴⁵⁶⁷⁸⁹₀₁", "①②③④⑤⑥⑦⑧⑨⓪⑴⑵", "፩፪፫፬፭፮፯፰፱፩፪፫", "🄀🄁🄂🄃🄄🄅🄆🄇🄈🄉🄊🄀"])(
  "digits that are not decimal also count as only digits: %j",
  (password) => {
    expect(notOnlyDigits(password)).toEqual({ key: "passwordOnlyDigits" });
  },
);
