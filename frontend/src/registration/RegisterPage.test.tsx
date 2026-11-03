import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
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

test("shows the terms and the marketing text as Markdown without interpreting HTML", async () => {
  const content =
    "**Cláusula 1**\n\nVer <https://example.com>.\n\n<b>negrita</b><script>x()</script>";
  const { fetcher } = fakeFetch(
    respondWith({
      ...OPTIONS,
      terms: { ...OPTIONS.terms, content },
      marketing: { ...OPTIONS.marketing, content },
    }),
  );
  renderPage(fetcher);

  await screen.findByText("Términos y condiciones");
  for (const title of ["Términos y condiciones", "Novedades por correo"]) {
    const details = screen.getByText(title).closest("details") as HTMLElement;
    expect(details.querySelector("strong")).toHaveTextContent("Cláusula 1");
    expect(details.querySelector("a")).toHaveAttribute("href", "https://example.com");
    expect(details.querySelectorAll("p")).toHaveLength(3);
    expect(details.querySelector("b, script")).toBeNull();
  }
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

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

function replies(...responses: (() => Promise<Response>)[]) {
  const sent: { url: string; body: unknown }[] = [];
  const fetcher = (url: RequestInfo | URL, init?: RequestInit) => {
    if (init?.method === "POST")
      sent.push({ url: String(url), body: JSON.parse(String(init.body)) });
    const next = responses.shift();
    return next ? next() : Promise.reject(new Error("unexpected call"));
  };
  return { sent, fetcher: fetcher as typeof fetch };
}

const reply = (status: number, body: unknown) => () => Promise.resolve(json(status, body));

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(await screen.findByRole("textbox", { name: "Nombre completo" }), "Ana Pérez");
  fireEvent.change(screen.getByLabelText(/^Fecha de nacimiento/), {
    target: { value: "1990-04-02" },
  });
  await user.type(screen.getByRole("textbox", { name: "Correo electrónico" }), "ana@planta.com");
  await user.selectOptions(screen.getByRole("combobox", { name: "País" }), "BR");
  await user.click(screen.getByRole("checkbox", { name: "Acepto los términos y condiciones" }));
}

describe("sending the form", () => {
  afterEach(() => {
    window.history.pushState(null, "", "/");
  });

  it("sends the data without marketing and goes to the verification", async () => {
    const user = userEvent.setup();
    const { sent, fetcher } = replies(
      reply(200, OPTIONS),
      reply(202, { public_id: "pid-1", message: "x" }),
    );
    renderPage(fetcher);

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    await waitFor(() => expect(window.location.pathname).toBe("/register/continue"));
    expect(window.location.hash).toBe("#pid-1");
    expect(sent).toEqual([
      {
        url: "/api/browser/v1/registration",
        body: {
          name: "Ana Pérez",
          birthdate: "1990-04-02",
          email: "ana@planta.com",
          country: "BR",
          terms: { accepted: true, version: "1", locale: "es" },
          language: "es",
        },
      },
    ]);
  });

  it("sends the marketing consent only when it is checked", async () => {
    const user = userEvent.setup();
    const { sent, fetcher } = replies(reply(200, OPTIONS), reply(202, { public_id: "p" }));
    renderPage(fetcher);

    await fillValidForm(user);
    await user.click(screen.getByRole("checkbox", { name: /^Quiero recibir novedades/ }));
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    await waitFor(() => expect(sent).toHaveLength(1));
    expect((sent[0].body as { marketing: unknown }).marketing).toEqual({
      version: "2",
      locale: "es",
    });
  });

  it("shows every server error under its field and goes to the first one", async () => {
    const user = userEvent.setup();
    const errors = {
      email: [{ code: "email_ip_domain", message: "x" }],
      name: [
        { code: "name_control_char", message: "x" },
        { code: "name_consecutive_spaces", message: "x" },
      ],
    };
    const { fetcher } = replies(reply(200, OPTIONS), reply(400, { errors }));
    renderPage(fetcher);

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    const name = screen.getByRole("textbox", { name: "Nombre completo" });
    await waitFor(() => expect(name).toHaveFocus());
    expect(name).toHaveAccessibleDescription(
      "El nombre no puede tener tabuladores, saltos de línea ni caracteres de control. El nombre no puede tener espacios seguidos.",
    );
    expect(screen.getByRole("textbox", { name: "Correo electrónico" })).toHaveAccessibleDescription(
      "El dominio del correo no puede ser una dirección IP.",
    );
    expect(scrolled[scrolled.length - 1]).toBe(name);
  });

  it("an error outside the fields gives the generic message", async () => {
    const user = userEvent.setup();
    const errors = { non_field_errors: [{ code: "invalid", message: "x" }] };
    const { fetcher } = replies(reply(200, OPTIONS), reply(400, { errors }));
    renderPage(fetcher);

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    expect(
      await screen.findByText(/Algo no ha funcionado\. Revisa los datos y vuelve a intentarlo\./),
    ).toHaveFocus();
  });

  it("with errors in and outside the fields, shows both", async () => {
    const user = userEvent.setup();
    const errors = {
      non_field_errors: [{ code: "invalid", message: "x" }],
      country: [{ code: "country_invalid", message: "x" }],
    };
    const { fetcher } = replies(reply(200, OPTIONS), reply(400, { errors }));
    renderPage(fetcher);

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    const country = screen.getByRole("combobox", { name: "País" });
    await waitFor(() => expect(country).toHaveFocus());
    expect(country).toHaveAccessibleDescription("Elige un país de la lista.");
    const shown = screen.getAllByText(/Algo no ha funcionado/);
    expect(shown.some((element) => element.getAttribute("tabindex") === "-1")).toBe(true);
  });

  it("while waiting for the answer, a second submission sends nothing", async () => {
    const user = userEvent.setup();
    const { sent, fetcher } = replies(reply(200, OPTIONS), () => new Promise<Response>(() => {}));
    renderPage(fetcher);

    await fillValidForm(user);
    fireEvent.submit(screen.getByRole("form"));
    fireEvent.submit(screen.getByRole("form"));

    await waitFor(() => expect(sent).toHaveLength(1));
    expect(sent).toHaveLength(1);
  });

  it.each([
    [() => Promise.reject(new TypeError("Failed to fetch")), /No se pudo conectar/],
    [reply(500, {}), /Algo falló en nuestro servidor/],
    [reply(400, { code: "invalid", message: "x" }), /Algo no ha funcionado/],
  ])("a failure gives a general message and keeps the data", async (failure, text) => {
    const user = userEvent.setup();
    const { fetcher } = replies(reply(200, OPTIONS), failure);
    renderPage(fetcher);

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    expect(await screen.findByText(text)).toHaveFocus();
    expect(screen.getByRole("textbox", { name: "Nombre completo" })).toHaveValue("Ana Pérez");
  });

  it("over the limit, counts down and enables the button again at zero", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const { fetcher } = replies(reply(200, OPTIONS), reply(429, { message: "x", retry_after: 2 }));
    renderPage(fetcher);

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: "Continuar" }));

    expect(
      await screen.findByText("Demasiados intentos. Vuelve a intentarlo en 2 s."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continuar" })).toBeDisabled();

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(screen.getByRole("button", { name: "Continuar" })).toBeEnabled();
    expect(screen.queryByText(/Demasiados intentos/)).toBeNull();
    vi.useRealTimers();
  });
});
