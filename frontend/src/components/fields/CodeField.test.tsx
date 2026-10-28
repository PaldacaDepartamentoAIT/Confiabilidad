import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";

import { CodeField } from "./CodeField";

test("is a single required field for one-time codes with a numeric keyboard", () => {
  render(<CodeField label="Verification code" required />);

  const input = screen.getByRole("textbox", { name: "Verification code" });
  expect(screen.getAllByRole("textbox")).toHaveLength(1);
  expect(input).toHaveAttribute("inputmode", "numeric");
  expect(input).toHaveAttribute("autocomplete", "one-time-code");
  expect(input).toHaveAttribute("aria-required", "true");
  expect(input).not.toHaveAttribute("maxlength");
});

test("keeps only the first 6 digits of what is typed", async () => {
  const user = userEvent.setup();
  const onValueChange = vi.fn();
  render(<CodeField label="Verification code" onValueChange={onValueChange} />);

  const input = screen.getByRole("textbox", { name: "Verification code" });
  await user.type(input, "1a2b3c4d5e6f7");

  expect(input).toHaveValue("123456");
  expect(onValueChange).toHaveBeenLastCalledWith("123456");
});

test("pasting replaces the whole code with the pasted digits", async () => {
  const user = userEvent.setup();
  render(<CodeField label="Verification code" />);

  const input = screen.getByRole<HTMLInputElement>("textbox", { name: "Verification code" });
  await user.type(input, "12");
  input.setSelectionRange(1, 1);
  await user.paste("98 76 54 32");

  expect(input).toHaveValue("987654");
});

test("cancels the browser's own paste so it cannot insert text in the middle", () => {
  render(<CodeField label="Verification code" />);

  const input = screen.getByRole("textbox", { name: "Verification code" });
  const notCancelled = fireEvent.paste(input, { clipboardData: { getData: () => "98 76 54" } });

  expect(notCancelled).toBe(false);
  expect(input).toHaveValue("987654");
});

test("pasting text without digits leaves the code as it was", async () => {
  const user = userEvent.setup();
  render(<CodeField label="Verification code" />);

  const input = screen.getByRole("textbox", { name: "Verification code" });
  await user.type(input, "12");
  await user.paste("abc");

  expect(input).toHaveValue("12");
});

test("completing the 6 digits neither submits nor moves the focus", async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn((event: React.FormEvent) => event.preventDefault());
  render(
    <form onSubmit={onSubmit}>
      <CodeField label="Verification code" />
      <button type="submit">Verify</button>
    </form>,
  );

  const input = screen.getByRole("textbox", { name: "Verification code" });
  await user.type(input, "123456");

  expect(onSubmit).not.toHaveBeenCalled();
  expect(input).toHaveFocus();
});

test("links an error to the field and forwards its ref", () => {
  const ref = createRef<HTMLInputElement>();
  render(<CodeField ref={ref} label="Verification code" error="Enter all 6 digits." />);

  const input = screen.getByRole("textbox", { name: "Verification code" });
  expect(ref.current).toBe(input);
  expect(input).toHaveAttribute("aria-invalid", "true");
  expect(input).toHaveAccessibleDescription("Enter all 6 digits.");
});
