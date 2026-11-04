import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { I18nextProvider } from "react-i18next";

import { App } from "../App";
import { createClient } from "../api/client";
import { createI18n } from "../i18n";

const STATUS = {
  code_expires_in: 900,
  resend_in: 60,
  resends_left: 5,
  locked: false,
  expired: false,
};
const OPTIONS = {
  countries: ["ES", "BR"],
  terms: { version: "1", locale: "es", content: "**Términos** del servicio." },
  marketing: { version: "1", locale: "es", content: "Novedades." },
};

type Answer = { status: number; body: unknown };

// Responde según la última parte de la ruta, como haría el servidor para cada pantalla.
function renderAt(path: string, answers: Record<string, Answer>) {
  window.history.replaceState(null, "", path);
  document.cookie = "csrftoken=token";
  const fetcher = (url: RequestInfo | URL) => {
    const route = String(url).split("?")[0].split("/").pop() ?? "";
    const answer = answers[route] ?? { status: 500, body: {} };
    return Promise.resolve(new Response(JSON.stringify(answer.body), { status: answer.status }));
  };
  const client = createClient({
    kind: "browser",
    appBaseUrl: "",
    language: () => "es",
    fetch: fetcher as typeof fetch,
  });
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <App client={client} />
    </I18nextProvider>,
  );
}

// jsdom no tiene canvas: axe no puede medir el contraste, así que se excluye de forma explícita.
async function violations(): Promise<string[]> {
  const results = await axe.run(document.body, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((violation) => violation.id);
}

const ok = (body: unknown): Answer => ({ status: 200, body });

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
});

afterEach(() => {
  delete (Element.prototype as Partial<Element>).scrollIntoView;
  window.history.replaceState(null, "", "/");
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
});

test("the empty form and the form with errors have no violations", async () => {
  const user = userEvent.setup();
  renderAt("/register", { options: ok(OPTIONS) });
  await screen.findByRole("combobox", { name: "País" });
  expect(await violations()).toEqual([]);

  await user.click(screen.getByRole("button", { name: "Continuar" }));

  expect(screen.getByRole("textbox", { name: "Nombre completo" })).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  expect(await violations()).toEqual([]);
});

test.each([
  ["normal", { status: ok(STATUS) }, "Escribe el código de verificación"],
  ["locked", { status: ok({ ...STATUS, locked: true }) }, "Escribe el código de verificación"],
  ["invalid link", { status: { status: 404, body: { code: "not_found" } } }, "Enlace no válido"],
])("the %s verification has no violations and no email", async (_, answers, heading) => {
  renderAt("/register/continue#pid-1", answers);

  await screen.findByRole("heading", { level: 1, name: heading });
  expect(await violations()).toEqual([]);
  expect(document.body.textContent).not.toContain("@");
});

test("the password step has no violations and no email", async () => {
  const user = userEvent.setup();
  renderAt("/register/continue#pid-1", { status: ok(STATUS), verify: ok({ result: "verified" }) });

  await user.type(await screen.findByRole("textbox", { name: "Código de verificación" }), "123456");
  await user.click(screen.getByRole("button", { name: "Verificar" }));

  await screen.findByRole("heading", { level: 2, name: "Elige tu contraseña" });
  expect(await violations()).toEqual([]);
  expect(document.body.textContent).not.toContain("@");
});

test("the account created screen has no violations and no email", async () => {
  renderAt("/register/done", {});

  await screen.findByRole("heading", { level: 1, name: "Cuenta creada" });
  expect(await violations()).toEqual([]);
  expect(document.body.textContent).not.toContain("@");
});
