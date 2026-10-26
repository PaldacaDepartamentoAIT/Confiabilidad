import { render, screen } from "@testing-library/react";
import { createRef } from "react";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../../i18n";
import { RequiredLegend } from "./RequiredLegend";
import { TextField } from "./TextField";

test("is named by its visible label", () => {
  render(<TextField label="Full name" autoComplete="name" />);

  const input = screen.getByRole("textbox", { name: "Full name" });
  expect(input).toHaveAttribute("type", "text");
  expect(input).toHaveAttribute("autocomplete", "name");
  expect(input).not.toHaveAttribute("aria-required");
  expect(screen.getByText("Full name").tagName).toBe("LABEL");
});

test("marks a required field for screen readers and with a visible asterisk", () => {
  render(<TextField label="Full name" required />);

  const input = screen.getByRole("textbox", { name: "Full name" });
  expect(input).toHaveAttribute("aria-required", "true");
  expect(input).not.toHaveAttribute("required");
  const asterisk = screen.getByText("*");
  expect(asterisk).toHaveAttribute("aria-hidden", "true");
  expect(asterisk.closest("label")).not.toBeNull();
});

test("an email field asks for email autocompletion and keyboard", () => {
  render(<TextField label="Email" type="email" />);

  const input = screen.getByRole("textbox", { name: "Email" });
  expect(input).toHaveAttribute("type", "email");
  expect(input).toHaveAttribute("autocomplete", "email");
  expect(input).toHaveAttribute("inputmode", "email");
});

test("links an error to the field and marks it as invalid", () => {
  const { rerender } = render(<TextField label="Email" type="email" error="Enter an email." />);

  const input = screen.getByRole("textbox", { name: "Email" });
  expect(input).toHaveAttribute("aria-invalid", "true");
  expect(input).toHaveAccessibleDescription("Enter an email.");
  expect(screen.getByText("Enter an email.")).toBeVisible();

  rerender(<TextField label="Email" type="email" />);

  expect(input).not.toHaveAttribute("aria-invalid");
  expect(input).not.toHaveAttribute("aria-describedby");
  expect(screen.queryByText("Enter an email.")).not.toBeInTheDocument();
});

test("forwards its ref and other attributes to the input", () => {
  const ref = createRef<HTMLInputElement>();
  render(<TextField ref={ref} label="Full name" name="name" defaultValue="Ana" />);

  expect(ref.current).toBe(screen.getByRole("textbox", { name: "Full name" }));
  expect(ref.current).toHaveAttribute("name", "name");
  expect(ref.current).toHaveValue("Ana");
});

test("the legend explains the asterisk in the active language", () => {
  render(
    <I18nextProvider i18n={createI18n("pt-BR")}>
      <RequiredLegend />
    </I18nextProvider>,
  );

  expect(screen.getByText("Os campos marcados com * são obrigatórios.")).toBeInTheDocument();
});
