import type { FieldError, ValidationKey } from "../forms/useFormValidation";

// Cada código del servidor tiene su clave propia; uno desconocido recibe el texto genérico (D-11).
const KEYS: Record<string, ValidationKey> = {
  required: "required",
  null: "required",
  blank: "required",
  invalid: "invalidValue",
  null_characters_not_allowed: "invalidCharacters",
  surrogate_characters_not_allowed: "invalidCharacters",
  max_length: "tooLong",
  email_domain_without_dot: "emailDomainWithoutDot",
  email_ip_domain: "emailIpDomain",
  name_empty: "nameEmpty",
  name_too_long: "nameTooLong",
  name_control_char: "nameControlChar",
  name_consecutive_spaces: "nameConsecutiveSpaces",
  birthdate_in_future: "birthdateInFuture",
  birthdate_under_minimum_age: "birthdateUnderMinimumAge",
  country_invalid: "countryInvalid",
  terms_not_accepted: "termsNotAccepted",
  document_not_found: "termsNotFound",
  wrong_kind: "termsWrongKind",
  no_current_version: "termsUnavailable",
  not_current_document: "termsChanged",
  wrong_code: "wrongCode",
  locked: "codeLocked",
  code_expired: "codeExpired",
  expired: "registrationExpired",
  resend_unavailable: "resendUnavailable",
  not_found: "linkNotFound",
  password_too_short: "passwordTooShort",
  password_too_similar: "passwordTooSimilar",
  password_too_common: "passwordTooCommon",
  password_entirely_numeric: "passwordOnlyDigits",
  password_pwned: "passwordPwned",
};

// Los mismos códigos tienen un texto más preciso en estos campos, como en el servidor.
const FIELD_KEYS: Record<string, ValidationKey> = {
  "email:invalid": "email",
  "email:max_length": "emailTooLong",
  "birthdate:invalid": "birthdateInvalid",
};

// Copia de las constantes de `backend/apps/accounts/validators.py`: el servidor no envía los valores
// con el error, solo el código.
const PARAMS: Partial<Record<ValidationKey, Record<string, number>>> = {
  nameTooLong: { max: 150 },
  birthdateUnderMinimumAge: { years: 18, days: 5 },
};

export function translateCode(code: string, field?: string): FieldError {
  const key = FIELD_KEYS[`${field}:${code}`] ?? KEYS[code] ?? "unknownError";
  const params = PARAMS[key];
  return params ? { key, params } : { key };
}

export function translateFieldErrors(
  errors: Record<string, readonly string[]>,
): Record<string, FieldError[]> {
  return Object.fromEntries(
    Object.entries(errors).map(([field, codes]) => [
      field,
      codes.map((code) => translateCode(code, field)),
    ]),
  );
}
