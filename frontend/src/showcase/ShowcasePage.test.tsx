import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { ShowcasePage } from "./ShowcasePage";

function renderPage(language = "es") {
  render(
    <I18nextProvider i18n={createI18n(language)}>
      <ShowcasePage />
    </I18nextProvider>,
  );
}

test("shows the sample form with its required fields and the asterisk legend", () => {
  renderPage("en");

  expect(screen.getByRole("heading", { level: 1, name: "Reliability" })).toBeInTheDocument();
  const form = screen.getByRole("form", { name: "Sample form" });
  expect(form).toHaveAttribute("novalidate");
  expect(screen.getByText("Fields marked with * are required.")).toBeInTheDocument();
  expect(screen.getByRole("textbox", { name: "Full name" })).toHaveAttribute(
    "aria-required",
    "true",
  );
  expect(screen.getByRole("textbox", { name: "Email" })).toHaveAttribute("type", "email");
  const password = screen.getByLabelText("Password", { exact: false });
  expect(password).toHaveAttribute("type", "password");
  expect(password).toHaveAttribute("autocomplete", "current-password");
  expect(password).toHaveAttribute("aria-required", "true");
  const code = screen.getByRole("textbox", { name: "Verification code" });
  expect(code).toHaveAttribute("autocomplete", "one-time-code");
  expect(code).toHaveAttribute("aria-required", "true");
});

test("the tab order goes through the language selector and then each field in order", async () => {
  const user = userEvent.setup();
  renderPage();

  const expected = [
    screen.getByRole("button", { name: "Español" }),
    screen.getByRole("button", { name: "Português (Brasil)" }),
    screen.getByRole("button", { name: "English" }),
    screen.getByRole("textbox", { name: "Nombre completo" }),
    screen.getByRole("textbox", { name: "Correo electrónico" }),
    screen.getByLabelText("Contraseña", { exact: false }),
    screen.getByRole("button", { name: "Mostrar contraseña" }),
    screen.getByRole("textbox", { name: "Código de verificación" }),
    screen.getByRole("button", { name: "Verificar" }),
  ];
  for (const element of expected) {
    await user.tab();
    expect(element).toHaveFocus();
  }
});

test("keeps typed values when the language changes", async () => {
  const user = userEvent.setup();
  renderPage();

  await user.type(screen.getByRole("textbox", { name: "Nombre completo" }), "Ana Pérez");
  await user.type(screen.getByRole("textbox", { name: "Correo electrónico" }), "ana@planta.com");
  await user.click(screen.getByRole("button", { name: "English" }));

  expect(screen.getByRole("textbox", { name: "Full name" })).toHaveValue("Ana Pérez");
  expect(screen.getByRole("textbox", { name: "Email" })).toHaveValue("ana@planta.com");
});

test("shows a field error when leaving the field and removes it once fixed", async () => {
  const user = userEvent.setup();
  renderPage();

  const email = screen.getByRole("textbox", { name: "Correo electrónico" });
  await user.type(email, "a@");
  await user.tab();

  expect(email).toHaveAttribute("aria-invalid", "true");
  expect(email).toHaveAccessibleDescription("Escribe un correo como nombre@empresa.com.");

  await user.type(email, "planta.com");
  await user.tab();

  expect(email).not.toHaveAttribute("aria-invalid");
  expect(email).not.toHaveAccessibleDescription();
});

test("an empty required field gets its error when left", async () => {
  const user = userEvent.setup();
  renderPage();

  await user.click(screen.getByRole("textbox", { name: "Nombre completo" }));
  await user.tab();

  expect(screen.getByRole("textbox", { name: "Nombre completo" })).toHaveAccessibleDescription(
    "Completa este campo.",
  );
});

test("an incomplete code gets its error when left", async () => {
  const user = userEvent.setup();
  renderPage();

  const code = screen.getByRole("textbox", { name: "Código de verificación" });
  await user.type(code, "12345");
  await user.tab();

  expect(code).toHaveAccessibleDescription("Escribe los 6 dígitos del código.");
});

test("a visible error follows the language change and keeps the field invalid", async () => {
  const user = userEvent.setup();
  renderPage();

  await user.type(screen.getByRole("textbox", { name: "Correo electrónico" }), "a@");
  await user.tab();
  await user.click(screen.getByRole("button", { name: "English" }));

  const email = screen.getByRole("textbox", { name: "Email" });
  expect(email).toHaveAttribute("aria-invalid", "true");
  expect(email).toHaveAccessibleDescription("Enter an email like name@company.com.");
});

test("the password is validated when leaving it together with its toggle", async () => {
  const user = userEvent.setup();
  renderPage();

  const password = screen.getByLabelText("Contraseña", { exact: false });
  await user.click(password);
  await user.tab();
  await user.tab({ shift: true });
  await user.tab();

  expect(password).not.toHaveAttribute("aria-invalid");

  await user.tab();

  expect(screen.getByRole("textbox", { name: "Código de verificación" })).toHaveFocus();
  expect(password).toHaveAccessibleDescription("Completa este campo.");
});

test("a filled password left from its toggle has no error", async () => {
  const user = userEvent.setup();
  renderPage();

  const password = screen.getByLabelText("Contraseña", { exact: false });
  await user.type(password, "s3cret");
  await user.tab();
  await user.tab();

  expect(password).not.toHaveAttribute("aria-invalid");
});

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByRole("textbox", { name: "Nombre completo" }), "Ana Pérez");
  await user.type(screen.getByRole("textbox", { name: "Correo electrónico" }), "ana@planta.com");
  await user.type(screen.getByLabelText("Contraseña", { exact: false }), "s3cret");
  await user.type(screen.getByRole("textbox", { name: "Código de verificación" }), "123456");
}

test("submitting with Enter shows every error and focuses the first invalid field", async () => {
  const user = userEvent.setup();
  renderPage();

  await user.type(screen.getByRole("textbox", { name: "Nombre completo" }), "Ana Pérez");
  await user.type(screen.getByLabelText("Contraseña", { exact: false }), "s3cret");
  await user.type(screen.getByRole("textbox", { name: "Código de verificación" }), "12345{Enter}");

  const email = screen.getByRole("textbox", { name: "Correo electrónico" });
  expect(email).toHaveFocus();
  expect(email).toHaveAccessibleDescription("Completa este campo.");
  expect(
    screen.getByRole("textbox", { name: "Código de verificación" }),
  ).toHaveAccessibleDescription("Escribe los 6 dígitos del código.");
});

test("submitting with the button behaves the same", async () => {
  const user = userEvent.setup();
  renderPage();

  await user.click(screen.getByRole("button", { name: "Verificar" }));

  expect(screen.getByRole("textbox", { name: "Nombre completo" })).toHaveFocus();
});

test("a valid submission shows the demo message and focuses it", async () => {
  const user = userEvent.setup();
  renderPage();

  await fillValidForm(user);
  await user.click(screen.getByRole("button", { name: "Verificar" }));

  const message = screen.getByText("Formulario de demostración", { exact: false }).closest("div");
  expect(message).toHaveTextContent("Información: Formulario de demostración: no se envían datos.");
  expect(message).toHaveFocus();
});

test("the next submission removes the general message", async () => {
  const user = userEvent.setup();
  renderPage();

  await fillValidForm(user);
  await user.click(screen.getByRole("button", { name: "Verificar" }));
  await user.clear(screen.getByRole("textbox", { name: "Nombre completo" }));
  await user.click(screen.getByRole("button", { name: "Verificar" }));

  expect(
    screen.queryByText("Formulario de demostración", { exact: false }),
  ).not.toBeInTheDocument();
});
