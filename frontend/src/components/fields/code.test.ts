import { CODE_LENGTH, extractPastedCode, normalizeTypedCode } from "./code";

test("the code has 6 digits", () => {
  expect(CODE_LENGTH).toBe(6);
});

test.each([
  ["123456", "123456"],
  ["12a３٤5 67", "123456"],
  ["０１２３４５６７８９", "012345"],
  ["٠١٢٣٤٥٦٧٨٩", "012345"],
  ["12-34", "1234"],
  ["abc", ""],
  ["", ""],
  ["۱۲۳", ""],
])("typing %j leaves %j", (typed, expected) => {
  expect(normalizeTypedCode(typed)).toBe(expected);
});

test.each([
  ["Tu código: 98-76 54 321", "987654"],
  ["98 76 54 32", "987654"],
  ["١٢٣٤٥٦", "123456"],
  ["12", "12"],
])("pasting %j gives %j", (pasted, expected) => {
  expect(extractPastedCode(pasted)).toBe(expected);
});

test.each(["sin números", "", "   ", "۱۲۳"])("pasting %j has no digits", (pasted) => {
  expect(extractPastedCode(pasted)).toBeNull();
});
