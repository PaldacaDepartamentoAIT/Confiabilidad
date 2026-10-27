import { render, screen } from "@testing-library/react";
import type { FocusEvent } from "react";
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

type SubmitFormProps = {
  onValid: (values: Record<"name" | "code", string>) => void;
  processing?: boolean;
  onFieldFocus?: (event: FocusEvent<HTMLInputElement>) => void;
};

function SubmitForm({ onValid, processing = false, onFieldFocus }: SubmitFormProps) {
  const { errors, handleSubmit } = useFormValidation(
    { name: [notEmpty], code: [notEmpty, longEnough] },
    { processing },
  );
  return (
    <form onSubmit={handleSubmit(onValid)}>
      <label>
        Name
        <input name="name" aria-invalid={errors.name ? true : undefined} onFocus={onFieldFocus} />
      </label>
      <label>
        Code
        <input name="code" aria-invalid={errors.code ? true : undefined} onFocus={onFieldFocus} />
      </label>
      <button type="submit">Send</button>
    </form>
  );
}

test("submitting validates every field and focuses the first invalid one in order", async () => {
  const user = userEvent.setup();
  const onValid = vi.fn();
  const invalidWhenFocused: (string | null)[] = [];
  render(
    <SubmitForm
      onValid={onValid}
      onFieldFocus={(event) => invalidWhenFocused.push(event.target.getAttribute("aria-invalid"))}
    />,
  );

  await user.type(screen.getByRole("textbox", { name: "Code" }), "1");
  invalidWhenFocused.length = 0;
  await user.click(screen.getByRole("button", { name: "Send" }));

  expect(onValid).not.toHaveBeenCalled();
  expect(screen.getByRole("textbox", { name: "Name" })).toHaveFocus();
  expect(screen.getByRole("textbox", { name: "Name" })).toHaveAttribute("aria-invalid", "true");
  expect(screen.getByRole("textbox", { name: "Code" })).toHaveAttribute("aria-invalid", "true");
  expect(invalidWhenFocused).toEqual(["true"]);
});

test("submitting with Enter from a field also validates", async () => {
  const user = userEvent.setup();
  const onValid = vi.fn();
  render(<SubmitForm onValid={onValid} />);

  await user.type(screen.getByRole("textbox", { name: "Name" }), "Ana");
  await user.type(screen.getByRole("textbox", { name: "Code" }), "12{Enter}");

  expect(onValid).not.toHaveBeenCalled();
  expect(screen.getByRole("textbox", { name: "Code" })).toHaveFocus();
});

test("a valid submission calls the handler with the values", async () => {
  const user = userEvent.setup();
  const onValid = vi.fn();
  render(<SubmitForm onValid={onValid} />);

  await user.type(screen.getByRole("textbox", { name: "Name" }), "Ana");
  await user.type(screen.getByRole("textbox", { name: "Code" }), "123");
  await user.click(screen.getByRole("button", { name: "Send" }));

  expect(onValid).toHaveBeenCalledWith({ name: "Ana", code: "123" });
});

test("while processing, a new submission is ignored", async () => {
  const user = userEvent.setup();
  const onValid = vi.fn();
  render(<SubmitForm onValid={onValid} processing />);

  await user.type(screen.getByRole("textbox", { name: "Name" }), "Ana");
  await user.type(screen.getByRole("textbox", { name: "Code" }), "123");
  await user.click(screen.getByRole("button", { name: "Send" }));

  expect(onValid).not.toHaveBeenCalled();
});
