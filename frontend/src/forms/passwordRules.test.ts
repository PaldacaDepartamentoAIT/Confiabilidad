import type { Validator } from "./useFormValidation";
import { newPasswordRules } from "./passwordRules";

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
