import { render, screen } from "@testing-library/react";
import axe from "axe-core";
import { createRef } from "react";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../../i18n";
import { CodeField } from "./CodeField";
import { PasswordField } from "./PasswordField";
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

test("a hint is shown under the field and describes it", () => {
  render(<TextField label="Name" hint="As written on your ID." />);

  const input = screen.getByRole("textbox", { name: "Name" });
  expect(screen.getByText("As written on your ID.")).toBeVisible();
  expect(input).toHaveAccessibleDescription("As written on your ID.");
});

test("with a hint and an error, the description contains both", () => {
  render(<TextField label="Name" hint="As written on your ID." error="Fill in this field." />);

  expect(screen.getByRole("textbox", { name: "Name" })).toHaveAccessibleDescription(
    "As written on your ID. Fill in this field.",
  );
});

test("a date field keeps its type and its label", () => {
  const { container } = render(<TextField label="Birthdate" type="date" name="birthdate" />);

  const input = container.querySelector("input");
  expect(input).toHaveAttribute("type", "date");
  expect(input).toHaveAccessibleName("Birthdate");
});

test("is laid out as in the design system: label, field, hint and error", () => {
  const { container } = render(
    <TextField label="Name" required hint="As written on your ID." error="Fill in this field." />,
  );

  const wrapper = container.firstElementChild;
  expect(wrapper).toHaveClass("fld");
  const label = screen.getByText("Name", { selector: "label" });
  expect(label).toHaveAttribute("data-ui", "field-label");
  expect(label.querySelector(".req")).toHaveTextContent("*");
  const input = screen.getByRole("textbox", { name: "Name" });
  expect(input).toHaveClass("field");
  expect(input).toHaveAttribute("data-ui", "field");
  expect(screen.getByText("As written on your ID.")).toHaveClass("help");
  const error = screen.getByText("Fill in this field.").closest("p");
  expect(error).toHaveClass("error-msg");
  expect(error?.querySelector("svg")).toHaveClass("lucide-circle-alert");
  expect(error?.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  expect([...(wrapper?.children ?? [])].map((child) => child.tagName)).toEqual([
    "LABEL",
    "INPUT",
    "P",
    "P",
  ]);
});

test("the class names given to the field are added to its own", () => {
  render(<TextField label="Code" className="mono" />);
  expect(screen.getByRole("textbox", { name: "Code" })).toHaveClass("field", "mono");
});

test("has no accessibility violations with a hint and an error", async () => {
  const { container } = render(
    <TextField label="Name" required hint="As written on your ID." error="Fill in this field." />,
  );
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});

describe("the fields built on TextField keep the design system look", () => {
  test("the password field's toggle is a secondary-style button inside the field", () => {
    const { container } = render(
      <I18nextProvider i18n={createI18n("en")}>
        <PasswordField label="Password" kind="current" />
      </I18nextProvider>,
    );

    const toggle = screen.getByRole("button", { name: "Show password (Password)" });
    expect(toggle).toHaveClass("btn", "btn-ghost", "hov");
    expect(container.firstElementChild).toHaveClass("fld");
    expect(container.firstElementChild).toContainElement(toggle);
    expect(screen.getByLabelText(/^Password/)).toHaveClass("field");
  });

  test("the verification code is written in the monospace font of the field", () => {
    render(<CodeField label="Code" />);
    expect(screen.getByRole("textbox", { name: "Code" })).toHaveClass("field", "mono");
  });

  test("the legend uses the help text style", () => {
    render(
      <I18nextProvider i18n={createI18n("en")}>
        <RequiredLegend />
      </I18nextProvider>,
    );
    expect(screen.getByText("Fields marked with * are required.")).toHaveClass("help");
  });
});
