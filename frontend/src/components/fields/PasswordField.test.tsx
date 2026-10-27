import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef, type ReactElement } from "react";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../../i18n";
import { PasswordField } from "./PasswordField";

function renderWithI18n(element: ReactElement) {
  return render(<I18nextProvider i18n={createI18n("en")}>{element}</I18nextProvider>);
}

// Nunca se ejecuta: solo comprueba en compilación que `kind` es obligatorio (RF-024).
export function missingKindDoesNotCompile() {
  // @ts-expect-error: kind is required
  return <PasswordField label="Password" />;
}

test.each([
  ["current", "current-password"],
  ["new", "new-password"],
] as const)("a %s password asks for %s autocompletion", (kind, autocomplete) => {
  renderWithI18n(<PasswordField label="Password" kind={kind} required />);

  const input = screen.getByLabelText("Password", { exact: false });
  expect(input).toHaveAttribute("type", "password");
  expect(input).toHaveAttribute("autocomplete", autocomplete);
  expect(input).toHaveAttribute("aria-required", "true");
});

test("shows and hides the password from the keyboard, keeping value and focus", async () => {
  const user = userEvent.setup();
  renderWithI18n(<PasswordField label="Password" kind="current" />);

  const input = screen.getByLabelText("Password");
  await user.type(input, "s3cret pass");
  await user.tab();
  const toggle = screen.getByRole("button", { name: "Show password" });
  expect(toggle).toHaveFocus();
  expect(toggle).toHaveAttribute("type", "button");
  expect(toggle).toHaveAttribute("aria-pressed", "false");

  await user.keyboard("{Enter}");

  expect(input).toHaveAttribute("type", "text");
  expect(input).toHaveValue("s3cret pass");
  expect(toggle).toHaveAttribute("aria-pressed", "true");
  expect(toggle).toHaveFocus();

  await user.keyboard(" ");

  expect(input).toHaveAttribute("type", "password");
  expect(input).toHaveValue("s3cret pass");
  expect(toggle).toHaveAttribute("aria-pressed", "false");
  expect(toggle).toHaveFocus();
});

test("links an error to the password input", () => {
  renderWithI18n(<PasswordField label="Password" kind="new" error="Fill in this field." />);

  const input = screen.getByLabelText("Password");
  expect(input).toHaveAttribute("aria-invalid", "true");
  expect(input).toHaveAccessibleDescription("Fill in this field.");
});

test("keeps the password away from spellcheckers and autocorrection, hidden or shown", async () => {
  const user = userEvent.setup();
  renderWithI18n(<PasswordField label="Password" kind="current" />);

  const input = screen.getByLabelText("Password");
  const expectProtected = () => {
    expect(input).toHaveAttribute("spellcheck", "false");
    expect(input).toHaveAttribute("autocapitalize", "off");
    expect(input).toHaveAttribute("autocorrect", "off");
  };
  expectProtected();

  await user.click(screen.getByRole("button", { name: "Show password" }));

  expect(input).toHaveAttribute("type", "text");
  expectProtected();
});

test("moving between the input and its toggle is not leaving the field", async () => {
  const user = userEvent.setup();
  const onBlur = vi.fn();
  renderWithI18n(
    <>
      <PasswordField label="Password" kind="current" onBlur={onBlur} />
      <button type="button">After</button>
    </>,
  );

  const input = screen.getByLabelText("Password");
  await user.click(input);
  await user.tab();
  expect(screen.getByRole("button", { name: "Show password" })).toHaveFocus();
  await user.tab({ shift: true });
  expect(input).toHaveFocus();
  await user.tab();

  expect(onBlur).not.toHaveBeenCalled();

  await user.tab();

  expect(screen.getByRole("button", { name: "After" })).toHaveFocus();
  expect(onBlur).toHaveBeenCalledTimes(1);
  expect(onBlur.mock.calls[0][0].target).toBe(input);
});

test("leaving the input towards anything but its toggle is leaving the field", async () => {
  const user = userEvent.setup();
  const onBlur = vi.fn();
  renderWithI18n(
    <>
      <PasswordField label="Password" kind="current" onBlur={onBlur} />
      <button type="button">After</button>
    </>,
  );

  const input = screen.getByLabelText("Password");
  await user.click(input);
  await user.click(screen.getByRole("button", { name: "After" }));

  expect(onBlur).toHaveBeenCalledTimes(1);
  expect(onBlur.mock.calls[0][0].target).toBe(input);
});

test("forwards its ref to the password input", () => {
  const ref = createRef<HTMLInputElement>();
  renderWithI18n(<PasswordField ref={ref} label="Password" kind="current" />);

  expect(ref.current).toBe(screen.getByLabelText("Password"));
});
