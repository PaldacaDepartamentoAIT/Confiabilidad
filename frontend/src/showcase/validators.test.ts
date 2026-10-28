import { en } from "../i18n/locales/en";
import { email, required, sixDigitCode } from "./validators";

test.each(["", "   ", "\t"])("required rejects %j", (value) => {
  expect(required(value)).toEqual({ key: "required" });
});

test("required accepts any non-blank text", () => {
  expect(required(" Ana ")).toBeNull();
});

test.each(["a@b", "ana.perez+planta@empresa.com", "ana@españa.es"])("email accepts %j", (value) => {
  expect(email(value)).toBeNull();
});

test.each(["a@@b", "@b", "a@", "a b@c", "a@b@c", "ab", "a@ b"])("email rejects %j", (value) => {
  expect(email(value)).toEqual({ key: "email" });
});

test.each(["123456", "000000"])("sixDigitCode accepts %j", (value) => {
  expect(sixDigitCode(value)).toBeNull();
});

test.each(["12345", "1234567", "12345a", ""])("sixDigitCode rejects %j", (value) => {
  expect(sixDigitCode(value)).toEqual({ key: "codeIncomplete" });
});

test("every rejection points to an existing text", () => {
  const keys = [required(""), email("x"), sixDigitCode("1")].map((error) => error?.key);
  keys.forEach((key) => expect(Object.keys(en.validation)).toContain(key));
});
