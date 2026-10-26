import { createI18n } from ".";

test("known keys type-check and unknown keys do not", () => {
  const i18n = createI18n("en");

  expect(i18n.t("validation.codeIncomplete")).toBe("Enter all 6 digits of the code.");
  // Si esta directiva deja de ser necesaria, `tsc` falla: las claves ya no se comprueban (RF-008).
  // @ts-expect-error: the key does not exist in the texts
  void i18n.t("validation.doesNotExist");
});
