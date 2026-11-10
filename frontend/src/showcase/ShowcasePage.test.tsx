import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { App } from "../App";
import { createI18n } from "../i18n";
import { THEME_STORAGE_KEY } from "../theme/theme";
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
  const password = screen.getByLabelText(/^Password/);
  expect(password).toHaveAttribute("type", "password");
  expect(password).toHaveAttribute("autocomplete", "current-password");
  expect(password).toHaveAttribute("aria-required", "true");
  const code = screen.getByRole("textbox", { name: "Verification code" });
  expect(code).toHaveAttribute("autocomplete", "one-time-code");
  expect(code).toHaveAttribute("aria-required", "true");
});

test("the tab order goes through the language selector, the theme button and then each field in order", async () => {
  const user = userEvent.setup();
  renderPage();

  const expected = [
    screen.getByRole("button", { name: "Español" }),
    screen.getByRole("button", { name: "Português (Brasil)" }),
    screen.getByRole("button", { name: "English" }),
    screen.getByRole("button", { name: /^Tema (claro|oscuro)\. Cambiar tema$/ }),
    screen.getByRole("textbox", { name: "Nombre completo" }),
    screen.getByRole("textbox", { name: "Correo electrónico" }),
    screen.getByLabelText(/^Contraseña/),
    screen.getByRole("button", { name: "Mostrar contraseña (Contraseña)" }),
    screen.getByLabelText(/^Nueva contraseña/),
    screen.getByRole("button", { name: "Mostrar contraseña (Nueva contraseña)" }),
    screen.getByRole("textbox", { name: "Código de verificación" }),
    screen.getByRole("button", { name: "Verificar" }),
    screen.getByRole("button", { name: "Mostrar error general de ejemplo" }),
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

  const password = screen.getByLabelText(/^Contraseña/);
  await user.click(password);
  await user.tab();
  await user.tab({ shift: true });
  await user.tab();

  expect(password).not.toHaveAttribute("aria-invalid");

  await user.tab();

  expect(screen.getByLabelText(/^Nueva contraseña/)).toHaveFocus();
  expect(password).toHaveAccessibleDescription("Completa este campo.");
});

test("a filled password left from its toggle has no error", async () => {
  const user = userEvent.setup();
  renderPage();

  const password = screen.getByLabelText(/^Contraseña/);
  await user.type(password, "s3cret");
  await user.tab();
  await user.tab();

  expect(password).not.toHaveAttribute("aria-invalid");
});

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByRole("textbox", { name: "Nombre completo" }), "Ana Pérez");
  await user.type(screen.getByRole("textbox", { name: "Correo electrónico" }), "ana@planta.com");
  await user.type(screen.getByLabelText(/^Contraseña/), "s3cret");
  await user.type(screen.getByLabelText(/^Nueva contraseña/), "turbina-compresor-7");
  await user.type(screen.getByRole("textbox", { name: "Código de verificación" }), "123456");
}

test("submitting with Enter shows every error and focuses the first invalid field", async () => {
  const user = userEvent.setup();
  renderPage();

  await user.type(screen.getByRole("textbox", { name: "Nombre completo" }), "Ana Pérez");
  await user.type(screen.getByLabelText(/^Contraseña/), "s3cret");
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

// Testing Library espera a sus propios `setTimeout`, que con temporizadores simulados no avanzan:
// se rellena con temporizadores reales y solo el envío (síncrono, con `fireEvent`) usa los simulados.
test("a valid submission processes for 3 seconds and then shows the demo message", async () => {
  const user = userEvent.setup();
  renderPage();
  await fillValidForm(user);
  await user.tab();
  const button = screen.getByRole("button", { name: "Verificar" });
  expect(button).toHaveFocus();

  vi.useFakeTimers();
  try {
    fireEvent.click(button);
    expect(button).toHaveAccessibleName("Procesando…");
    expect(button).toHaveFocus();

    fireEvent.click(button);
    act(() => vi.advanceTimersByTime(2999));
    expect(button).toHaveAccessibleName("Procesando…");
    expect(screen.queryByText("Formulario de demostración", { exact: false })).toBeNull();

    act(() => vi.advanceTimersByTime(1));
  } finally {
    vi.useRealTimers();
  }

  expect(button).toHaveAccessibleName("Verificar");
  const message = screen.getByText("Formulario de demostración", { exact: false }).closest("div");
  expect(message).toHaveTextContent("Información: Formulario de demostración: no se envían datos.");
  expect(message).toHaveFocus();
});

test("a second submission while processing does not restart the wait", async () => {
  const user = userEvent.setup();
  renderPage();
  await fillValidForm(user);
  const button = screen.getByRole("button", { name: "Verificar" });

  vi.useFakeTimers();
  try {
    fireEvent.click(button);
    act(() => vi.advanceTimersByTime(2000));
    fireEvent.click(button);
    act(() => vi.advanceTimersByTime(1000));
  } finally {
    vi.useRealTimers();
  }

  expect(screen.getByText("Formulario de demostración", { exact: false })).toBeInTheDocument();
});

test("the next submission removes the general message", async () => {
  const user = userEvent.setup();
  renderPage();
  await fillValidForm(user);
  const button = screen.getByRole("button", { name: "Verificar" });

  vi.useFakeTimers();
  try {
    fireEvent.click(button);
    act(() => vi.advanceTimersByTime(3000));
  } finally {
    vi.useRealTimers();
  }
  expect(screen.getByText("Formulario de demostración", { exact: false })).toBeInTheDocument();

  await user.clear(screen.getByRole("textbox", { name: "Nombre completo" }));
  await user.click(button);

  expect(
    screen.queryByText("Formulario de demostración", { exact: false }),
  ).not.toBeInTheDocument();
});

test("the new password shows its rules and checks them when left", async () => {
  const user = userEvent.setup();
  renderPage();

  const newPassword = screen.getByLabelText(/^Nueva contraseña/);
  expect(newPassword).toHaveAttribute("autocomplete", "new-password");
  expect(newPassword).toHaveAttribute("aria-required", "true");
  expect(newPassword).toHaveAccessibleDescription("Al menos 12 caracteres, no solo números.");

  await user.type(newPassword, "abc");
  await user.click(screen.getByRole("textbox", { name: "Código de verificación" }));
  expect(newPassword).toHaveAccessibleDescription(
    "Al menos 12 caracteres, no solo números. Usa al menos 12 caracteres.",
  );

  await user.clear(newPassword);
  await user.type(newPassword, "123456789012");
  await user.click(screen.getByRole("textbox", { name: "Código de verificación" }));
  expect(newPassword).toHaveAccessibleDescription(
    "Al menos 12 caracteres, no solo números. No uses solo números.",
  );
});

test("the current password does not apply the new password rules", async () => {
  const user = userEvent.setup();
  renderPage();

  const password = screen.getByLabelText(/^Contraseña/);
  await user.type(password, "abc");
  await user.click(screen.getByRole("textbox", { name: "Código de verificación" }));

  expect(password).not.toHaveAttribute("aria-invalid");
});

test("submitting with a short new password focuses it", async () => {
  const user = userEvent.setup();
  renderPage();

  await fillValidForm(user);
  await user.clear(screen.getByLabelText(/^Nueva contraseña/));
  await user.type(screen.getByLabelText(/^Nueva contraseña/), "corta");
  await user.click(screen.getByRole("button", { name: "Verificar" }));

  expect(screen.getByLabelText(/^Nueva contraseña/)).toHaveFocus();
});

test("in the whole app, entering the processing state is announced to screen readers", async () => {
  const user = userEvent.setup();
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <App />
    </I18nextProvider>,
  );
  await fillValidForm(user);
  const status = screen.getByRole("status");
  expect(status).toBeEmptyDOMElement();

  vi.useFakeTimers();
  try {
    fireEvent.click(screen.getByRole("button", { name: "Verificar" }));
    act(() => vi.advanceTimersByTime(0));
    expect(status).toHaveTextContent("Procesando");
  } finally {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  }
});

test("the sample error button shows the too many attempts error and focuses it", async () => {
  const user = userEvent.setup();
  renderPage();

  await user.click(screen.getByRole("button", { name: "Mostrar error general de ejemplo" }));

  const message = screen.getByText("Demasiados intentos", { exact: false }).closest("div");
  expect(message).toHaveTextContent(
    "Error: Demasiados intentos. Espera unos minutos y vuelve a intentarlo.",
  );
  expect(message).toHaveFocus();
});

test("the sample error follows the language change and the next submission removes it", async () => {
  const user = userEvent.setup();
  renderPage();

  await user.click(screen.getByRole("button", { name: "Mostrar error general de ejemplo" }));
  await user.click(screen.getByRole("button", { name: "English" }));

  expect(screen.getByText("Too many attempts", { exact: false }).closest("div")).toHaveTextContent(
    "Error: Too many attempts. Wait a few minutes and try again.",
  );

  await user.click(screen.getByRole("button", { name: "Verify" }));

  expect(screen.queryByText("Too many attempts", { exact: false })).not.toBeInTheDocument();
});

test("has a theme button that saves the chosen theme in the storage it receives", async () => {
  const user = userEvent.setup();
  const values = new Map<string, string>();
  const storage = {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => void values.set(key, value),
    removeItem: (key: string) => void values.delete(key),
  };
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <ShowcasePage storage={storage} />
    </I18nextProvider>,
  );

  await user.click(screen.getByRole("button", { name: /^Tema (claro|oscuro)\. Cambiar tema$/ }));

  expect(["light", "dark"]).toContain(values.get(THEME_STORAGE_KEY));
  expect(document.documentElement).toHaveAttribute("data-theme", values.get(THEME_STORAGE_KEY));
  document.documentElement.removeAttribute("data-theme");
});

test("the catalog shows the three block variants, the chips and the four alarm shapes", () => {
  renderPage("en");

  const catalog = screen.getByRole("region", { name: "Bloques, etiquetas y formas de alarma" });
  expect(catalog).toHaveAttribute("lang", "es");
  const blocks = catalog.querySelectorAll("[data-ui='block']");
  expect(blocks).toHaveLength(3);
  expect(catalog.querySelector(".block.featured")).toBeInTheDocument();
  expect(catalog.querySelector(".block.alert")).toBeInTheDocument();
  expect(catalog.querySelectorAll("[data-ui='chip']").length).toBeGreaterThanOrEqual(3);
  const shapes = [...catalog.querySelectorAll("[data-shape]")].map((shape) =>
    shape.getAttribute("data-shape"),
  );
  expect(shapes.sort()).toEqual(["diamond", "hollow-square", "square", "triangle"]);
  expect(catalog.querySelector("[data-ui='counter']")).toBeInTheDocument();
});

test("the catalog adds no extra stops to the keyboard order", async () => {
  const user = userEvent.setup();
  renderPage();
  const catalog = screen.getByRole("region", { name: "Bloques, etiquetas y formas de alarma" });
  for (let i = 0; i < 12; i += 1) await user.tab();
  expect(catalog.contains(document.activeElement)).toBe(false);
});

test("the catalog shows buttons in both variants and while processing, and the notices", () => {
  renderPage("en");

  const catalog = screen.getByRole("region", { name: "Botones y avisos" });
  expect(catalog).toHaveAttribute("lang", "es");
  expect(catalog.querySelectorAll("[data-ui='button-primary']").length).toBeGreaterThanOrEqual(2);
  expect(catalog.querySelectorAll("[data-ui='button-secondary']").length).toBeGreaterThanOrEqual(1);
  expect(catalog.querySelector("[aria-disabled='true']")).toBeInTheDocument();
  expect(catalog.querySelectorAll("[data-ui='notice']")).toHaveLength(2);
  expect(catalog.querySelector("[data-ui='notice'] .lucide-check")).toBeInTheDocument();
  expect(catalog.querySelector("[data-ui='notice'] .lucide-info")).toBeInTheDocument();
  const shapes = [...catalog.querySelectorAll("[data-ui='alarm-notice'] [data-shape]")].map(
    (shape) => shape.getAttribute("data-shape"),
  );
  expect(shapes.sort()).toEqual(["diamond", "hollow-square", "square", "triangle"]);
  expect(
    within(catalog).getByRole("button", { name: "Ver alarma" }).closest("[data-ui='alarm-notice']"),
  ).toBeInTheDocument();
});

test("the catalog shows text, password and code fields, a field with an error and the checkbox", () => {
  renderPage("en");

  const catalog = screen.getByRole("region", { name: "Campos" });
  expect(catalog).toHaveAttribute("lang", "es");
  expect(within(catalog).getByRole("textbox", { name: "Razón social" })).toBeInTheDocument();
  expect(within(catalog).getByLabelText(/^Clave de acceso/)).toHaveAttribute("type", "password");
  expect(within(catalog).getByRole("textbox", { name: "Código" })).toHaveClass("mono");
  const invalid = catalog.querySelectorAll("[data-ui='field'][aria-invalid='true']");
  expect(invalid).toHaveLength(1);
  expect(invalid[0]).toHaveAccessibleDescription("El NIF/CIF debe tener 9 caracteres.");
  const boxes = within(catalog).getAllByRole("checkbox");
  expect(boxes).toHaveLength(3);
  expect(boxes.filter((box) => (box as HTMLInputElement).checked)).toHaveLength(1);
  expect(catalog.querySelector("[data-ui='checkbox'][aria-invalid='true']")).toBeInTheDocument();
});

test("the catalog shows the language button and a generic menu that keeps its choice", async () => {
  const user = userEvent.setup();
  renderPage("en");

  const catalog = screen.getByRole("region", { name: "Menú e idioma" });
  expect(catalog).toHaveAttribute("lang", "es");
  expect(within(catalog).getAllByRole("combobox")).toHaveLength(2);

  await user.click(within(catalog).getByRole("combobox", { name: "Language: English" }));
  expect(
    within(catalog)
      .getAllByRole("option")
      .map((option) => option.textContent),
  ).toEqual(["Español", "Português (Brasil)", "English"]);
  await user.keyboard("{Escape}");

  const plants = within(catalog).getByRole("combobox", { name: "Planta: Norte" });
  await user.click(plants);
  await user.click(within(catalog).getByRole("option", { name: "Sur" }));
  expect(within(catalog).getByRole("combobox", { name: "Planta: Sur" })).toBeInTheDocument();
});
