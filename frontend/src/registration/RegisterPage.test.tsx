import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { createClient } from "../api/client";
import type { RegistrationOptions } from "../api/registration";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { createI18n } from "../i18n";
import { RegisterPage } from "./RegisterPage";

const OPTIONS: RegistrationOptions = {
  countries: ["ES", "BR", "CL"],
  terms: { version: "1", locale: "es", content: "Texto de los términos." },
  marketing: { version: "2", locale: "es", content: "Texto del marketing." },
};

function fakeFetch(response: () => Promise<Response>) {
  const calls: string[] = [];
  const fetcher = (url: RequestInfo | URL, init?: RequestInit) => {
    calls.push(`${init?.method ?? "GET"} ${String(url)}`);
    return response();
  };
  return { calls, fetcher: fetcher as typeof fetch };
}

function respondWith(body: unknown) {
  return () => Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
}

function renderPage(fetcher: typeof fetch, language = "es") {
  const i18n = createI18n(language);
  const client = createClient({
    kind: "browser",
    appBaseUrl: "",
    language: () => i18n.language,
    fetch: fetcher,
  });
  render(
    <I18nextProvider i18n={i18n}>
      <LiveAnnouncer>
        <RegisterPage client={client} />
      </LiveAnnouncer>
    </I18nextProvider>,
  );
}

const scrolled: Element[] = [];

beforeEach(() => {
  scrolled.length = 0;
  Element.prototype.scrollIntoView = function (this: Element) {
    scrolled.push(this);
  };
});

afterEach(() => {
  delete (Element.prototype as Partial<Element>).scrollIntoView;
});

test("loads the options and shows every field, with the countries by name in order", async () => {
  const { calls, fetcher } = fakeFetch(respondWith(OPTIONS));
  renderPage(fetcher);

  const country = await screen.findByRole("combobox", { name: "País" });
  expect(calls).toEqual(["GET /api/browser/v1/registration/options?language=es"]);
  expect(screen.getByRole("heading", { level: 1, name: "Crea tu cuenta" })).toBeInTheDocument();
  expect(screen.getByRole("textbox", { name: "Nombre completo" })).toHaveAttribute(
    "autocomplete",
    "name",
  );
  expect(screen.getByLabelText(/^Fecha de nacimiento/)).toHaveAttribute("type", "date");
  expect(screen.getByRole("textbox", { name: "Correo electrónico" })).toHaveAttribute(
    "type",
    "email",
  );
  expect(country).toHaveAttribute("aria-required", "true");
  expect(screen.getAllByRole("option").map((option) => option.textContent)).toEqual([
    "Elige un país",
    "Brasil",
    "Chile",
    "España",
  ]);
  expect(
    screen.getByRole("checkbox", { name: "Acepto los términos y condiciones" }),
  ).toHaveAttribute("aria-required", "true");
  const marketing = screen.getByRole("checkbox", { name: /^Quiero recibir novedades/ });
  expect(marketing).not.toBeChecked();
  expect(marketing).not.toHaveAttribute("aria-required");
});

test("names the countries in the active language", async () => {
  const { fetcher } = fakeFetch(respondWith(OPTIONS));
  renderPage(fetcher, "pt-BR");

  await screen.findByRole("combobox", { name: "País" });
  expect(screen.getByRole("option", { name: "Espanha" })).toHaveValue("ES");
});

test("gives access to the text of the terms and of the marketing consent", async () => {
  const user = userEvent.setup();
  const { fetcher } = fakeFetch(respondWith(OPTIONS));
  renderPage(fetcher);

  await user.click(await screen.findByText("Términos y condiciones"));
  expect(screen.getByText("Texto de los términos.")).toBeVisible();
  await user.click(screen.getByText("Novedades por correo"));
  expect(screen.getByText("Texto del marketing.")).toBeVisible();
});

test("without a marketing document there is no marketing checkbox", async () => {
  const { fetcher } = fakeFetch(respondWith({ ...OPTIONS, marketing: null }));
  renderPage(fetcher);

  await screen.findByRole("combobox", { name: "País" });
  expect(screen.queryByRole("checkbox", { name: /^Quiero recibir novedades/ })).toBeNull();
  expect(screen.queryByText("Novedades por correo")).toBeNull();
});

test("without terms in force there is no form, only the message", async () => {
  const { fetcher } = fakeFetch(respondWith({ ...OPTIONS, terms: null }));
  renderPage(fetcher);

  expect(
    await screen.findByText(/Ahora mismo no es posible registrarse: no hay términos vigentes\./),
  ).toBeInTheDocument();
  expect(screen.queryByRole("form")).toBeNull();
});

test("if the options cannot be loaded, it says so", async () => {
  const { fetcher } = fakeFetch(() => Promise.reject(new TypeError("Failed to fetch")));
  renderPage(fetcher);

  expect(
    await screen.findByText(/No se pudo conectar\. Revisa tu conexión y vuelve a intentarlo\./),
  ).toBeInTheDocument();
});

test("submitting it empty shows every error, scrolls to the first one and sends nothing", async () => {
  const user = userEvent.setup();
  const { calls, fetcher } = fakeFetch(respondWith(OPTIONS));
  renderPage(fetcher);
  await screen.findByRole("combobox", { name: "País" });

  await user.click(screen.getByRole("button", { name: "Continuar" }));

  const name = screen.getByRole("textbox", { name: "Nombre completo" });
  expect(name).toHaveAccessibleDescription("Completa este campo.");
  expect(screen.getByLabelText(/^Fecha de nacimiento/)).toHaveAccessibleDescription(
    "Completa este campo.",
  );
  expect(screen.getByRole("textbox", { name: "Correo electrónico" })).toHaveAccessibleDescription(
    "Completa este campo.",
  );
  expect(screen.getByRole("combobox", { name: "País" })).toHaveAccessibleDescription(
    "Elige un país de la lista.",
  );
  expect(
    screen.getByRole("checkbox", { name: "Acepto los términos y condiciones" }),
  ).toHaveAccessibleDescription("Debes aceptar los términos y condiciones.");
  expect(scrolled).toEqual([name]);
  expect(name).toHaveFocus();
  expect(calls).toHaveLength(1);
});

test("an email without the shape of an address is rejected before sending", async () => {
  const user = userEvent.setup();
  const { fetcher } = fakeFetch(respondWith(OPTIONS));
  renderPage(fetcher);

  await user.type(await screen.findByRole("textbox", { name: "Correo electrónico" }), "ana");
  await user.tab();

  expect(screen.getByRole("textbox", { name: "Correo electrónico" })).toHaveAccessibleDescription(
    "Escribe un correo como nombre@empresa.com.",
  );
});
