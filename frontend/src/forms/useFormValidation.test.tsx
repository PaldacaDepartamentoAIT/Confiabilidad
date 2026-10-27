import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { useFormValidation, type FieldError, type Validator } from "./useFormValidation";

const notEmpty: Validator = (value) => (value.trim() ? null : { key: "required" });
const longEnough: Validator = (value) =>
  value.length >= 3 ? null : { key: "codeIncomplete", params: { length: 3 } };

let latestErrors: Partial<Record<"name" | "code", FieldError>> = {};

function SampleForm() {
  const { errors, onBlur } = useFormValidation({
    name: [notEmpty],
    code: [notEmpty, longEnough],
  });
  latestErrors = errors;
  return (
    <form>
      <label>
        Name
        <input onBlur={onBlur("name")} />
      </label>
      <label>
        Code
        <input onBlur={onBlur("code")} />
      </label>
    </form>
  );
}

test("validates a field when leaving it, even before any submission", async () => {
  const user = userEvent.setup();
  render(<SampleForm />);

  await user.click(screen.getByRole("textbox", { name: "Name" }));
  await user.tab();

  expect(latestErrors).toEqual({ name: { key: "required" } });
});

test("only the field that is left is validated", async () => {
  const user = userEvent.setup();
  render(<SampleForm />);

  await user.click(screen.getByRole("textbox", { name: "Code" }));
  await user.keyboard("12");
  await user.tab();

  expect(latestErrors).toEqual({ code: { key: "codeIncomplete", params: { length: 3 } } });
});

test("reports the first failing rule and removes the error once the field is fixed", async () => {
  const user = userEvent.setup();
  render(<SampleForm />);

  const code = screen.getByRole("textbox", { name: "Code" });
  await user.click(code);
  await user.tab();
  expect(latestErrors.code).toEqual({ key: "required" });

  await user.click(code);
  await user.keyboard("123");
  await user.tab();

  expect(latestErrors).toEqual({});
});
