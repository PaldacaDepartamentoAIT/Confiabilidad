import { CODE_LENGTH } from "../components/fields/code";
import type { Validator } from "../forms/useFormValidation";

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+$/;
const CODE_PATTERN = new RegExp(`^\\d{${CODE_LENGTH}}$`);

export const required: Validator = (value) => (value.trim() ? null : { key: "required" });

export const email: Validator = (value) => (EMAIL_PATTERN.test(value) ? null : { key: "email" });

export const sixDigitCode: Validator = (value) =>
  CODE_PATTERN.test(value) ? null : { key: "codeIncomplete" };
