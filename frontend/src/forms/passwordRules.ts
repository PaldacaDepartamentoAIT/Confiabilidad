import type { Validator } from "./useFormValidation";

// Copia a mano las reglas del servidor que se pueden comprobar aquí (RF-026, D-18, S-11).
const MIN_LENGTH = 12;
const ONLY_DIGITS = /^\p{Nd}+$/u;

// Se cuenta por punto de código, como `len()` en Python, no por unidades UTF-16.
const minimumLength: Validator = (value) =>
  Array.from(value).length >= MIN_LENGTH ? null : { key: "passwordTooShort" };

const notOnlyDigits: Validator = (value) =>
  ONLY_DIGITS.test(value) ? { key: "passwordOnlyDigits" } : null;

export const newPasswordRules: readonly Validator[] = [minimumLength, notOnlyDigits];
