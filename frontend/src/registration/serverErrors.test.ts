import { createI18n } from "../i18n";
import { translateCode, translateFieldErrors } from "./serverErrors";

// Los códigos de `backend/apps/accounts/api/messages.py` (ERRORS); si el servidor añade uno, va aquí.
const SERVER_CODES: [string, string][] = [
  ["required", "required"],
  ["null", "required"],
  ["blank", "required"],
  ["invalid", "invalidValue"],
  ["null_characters_not_allowed", "invalidCharacters"],
  ["surrogate_characters_not_allowed", "invalidCharacters"],
  ["max_length", "tooLong"],
  ["email_domain_without_dot", "emailDomainWithoutDot"],
  ["email_ip_domain", "emailIpDomain"],
  ["name_empty", "nameEmpty"],
  ["name_too_long", "nameTooLong"],
  ["name_control_char", "nameControlChar"],
  ["name_consecutive_spaces", "nameConsecutiveSpaces"],
  ["birthdate_in_future", "birthdateInFuture"],
  ["birthdate_under_minimum_age", "birthdateUnderMinimumAge"],
  ["country_invalid", "countryInvalid"],
  ["terms_not_accepted", "termsNotAccepted"],
  ["document_not_found", "termsNotFound"],
  ["wrong_kind", "termsWrongKind"],
  ["no_current_version", "termsUnavailable"],
  ["not_current_document", "termsChanged"],
  ["wrong_code", "wrongCode"],
  ["locked", "codeLocked"],
  ["code_expired", "codeExpired"],
  ["expired", "registrationExpired"],
  ["resend_unavailable", "resendUnavailable"],
  ["not_found", "linkNotFound"],
  ["password_too_short", "passwordTooShort"],
  ["password_too_similar", "passwordTooSimilar"],
  ["password_too_common", "passwordTooCommon"],
  ["password_entirely_numeric", "passwordOnlyDigits"],
  ["password_pwned", "passwordPwned"],
];

test.each(SERVER_CODES)("the server code %s is shown with the key %s", (code, key) => {
  expect(translateCode(code).key).toBe(key);
});

test.each([
  ["email", "invalid", "email"],
  ["email", "max_length", "emailTooLong"],
  ["birthdate", "invalid", "birthdateInvalid"],
  ["name", "invalid", "invalidValue"],
])("on the field %s, the code %s has its own key %s", (field, code, key) => {
  expect(translateCode(code, field).key).toBe(key);
});

test("an unknown code gets the generic text", () => {
  expect(translateCode("brand_new_code")).toEqual({ key: "unknownError" });
});

test("the texts with numbers receive the server values", () => {
  expect(translateCode("name_too_long")).toEqual({ key: "nameTooLong", params: { max: 150 } });
  expect(translateCode("birthdate_under_minimum_age")).toEqual({
    key: "birthdateUnderMinimumAge",
    params: { years: 18, days: 5 },
  });
  expect(translateCode("wrong_code")).toEqual({ key: "wrongCode" });

  const i18n = createI18n("es");
  const { key, params } = translateCode("birthdate_under_minimum_age");
  expect(i18n.t(`validation.${key}`, params)).toBe(
    "Debes tener al menos 18 años y 5 días para registrarte.",
  );
});

test("translates every error of every field, in the order received", () => {
  expect(
    translateFieldErrors({
      password: ["password_too_common", "password_pwned"],
      email: ["invalid"],
    }),
  ).toEqual({
    password: [{ key: "passwordTooCommon" }, { key: "passwordPwned" }],
    email: [{ key: "email" }],
  });
});
