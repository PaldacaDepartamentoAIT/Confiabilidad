import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import type { SessionInfo } from "../api/auth";
import { createClient } from "../api/client";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { createI18n } from "../i18n";
import { LoginPage } from "./LoginPage";

function json(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

function renderLogin(
  fetcher: typeof fetch,
  onAuthenticated?: (session: SessionInfo) => void,
  language = "es",
) {
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
        <LoginPage client={client} onAuthenticated={onAuthenticated} />
      </LiveAnnouncer>
    </I18nextProvider>,
  );
}

beforeEach(() => {
  window.history.pushState(null, "", "/login");
  Element.prototype.scrollIntoView = () => {};
});

afterEach(() => {
  delete (Element.prototype as Partial<Element>).scrollIntoView;
});

test("valida al salir y al enviar sin llamar al servidor y enfoca el primer campo con error", async () => {
  const calls: string[] = [];
  const fetcher: typeof fetch = (url) => {
    calls.push(String(url));
    return Promise.resolve(json(200, {}));
  };
  renderLogin(fetcher);

  const emailInput = screen.getByRole("textbox", { name: "Correo electrónico" });
  const passwordInput = screen.getByLabelText(/^Contraseña/);

  fireEvent.blur(emailInput);
  expect(screen.getByText("Completa este campo.")).toBeInTheDocument();

  await userEvent.type(emailInput, "invalido");
  fireEvent.blur(emailInput);
  expect(screen.getByText("Escribe un correo como nombre@empresa.com.")).toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));
  expect(calls).toEqual([]);
  expect(emailInput).toHaveFocus();
  expect(passwordInput).toHaveAttribute("aria-invalid", "true");
});

test("vacía la contraseña y conserva el correo ante invalid_credentials, pero la conserva ante bloqueo o red", async () => {
  let response: () => Promise<Response> = () =>
    Promise.resolve(json(400, { code: "invalid_credentials", message: "x" }));
  renderLogin(() => response());

  const emailInput = screen.getByRole("textbox", {
    name: "Correo electrónico",
  }) as HTMLInputElement;
  const passwordInput = screen.getByLabelText(/^Contraseña/) as HTMLInputElement;

  await userEvent.type(emailInput, "ana@empresa.com");
  await userEvent.type(passwordInput, "secreto123");
  await userEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));

  expect(
    await screen.findByText(/El correo o la contraseña no son correctos\./),
  ).toBeInTheDocument();
  expect(emailInput.value).toBe("ana@empresa.com");
  expect(passwordInput.value).toBe("");

  response = () => Promise.resolve(json(400, { code: "too_many_login_attempts", message: "x" }));
  await userEvent.type(passwordInput, "secreto123");
  await userEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));

  expect(
    await screen.findByText(/Has superado el máximo de intentos fallidos\./),
  ).toBeInTheDocument();
  expect(emailInput.value).toBe("ana@empresa.com");
  expect(passwordInput.value).toBe("secreto123");

  response = () => Promise.reject(new TypeError("offline"));
  await userEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));
  expect(await screen.findByText(/No se pudo conectar\./)).toBeInTheDocument();
  expect(emailInput.value).toBe("ana@empresa.com");
});

test("muestra cuenta atrás ante 429 y desactiva el botón hasta llegar a cero", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  try {
    renderLogin(() => Promise.resolve(json(429, { message: "x", retry_after: 2 })));
    fireEvent.change(screen.getByRole("textbox", { name: "Correo electrónico" }), {
      target: { value: "ana@empresa.com" },
    });
    fireEvent.change(screen.getByLabelText(/^Contraseña/), {
      target: { value: "secreto123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));

    expect(
      await screen.findByText("Demasiados intentos. Vuelve a intentarlo en 2 s."),
    ).toBeInTheDocument();
    const submit = screen.getByRole("button", { name: "Iniciar sesión" });
    expect(submit).toBeDisabled();

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(submit).toBeEnabled();
  } finally {
    vi.useRealTimers();
  }
});

test("navega a /register con el enlace y redirige a / o /terms al autenticar", async () => {
  let termsStatus: "accepted" | "not_accepted" = "accepted";
  const sessions: SessionInfo[] = [];
  renderLogin(
    () =>
      Promise.resolve(
        json(200, {
          user: { email: "ana@empresa.com", name: "Ana" },
          terms_status: termsStatus,
          terms: null,
        }),
      ),
    (info) => sessions.push(info),
  );

  await userEvent.click(screen.getByRole("link", { name: "Crear una cuenta" }));
  expect(window.location.pathname).toBe("/register");

  await userEvent.type(
    screen.getByRole("textbox", { name: "Correo electrónico" }),
    "ana@empresa.com",
  );
  await userEvent.type(screen.getByLabelText(/^Contraseña/), "secreto123");
  await userEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));
  expect(window.location.pathname).toBe("/");
  expect(sessions).toHaveLength(1);

  termsStatus = "not_accepted";
  await userEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));
  expect(window.location.pathname).toBe("/terms");
});
