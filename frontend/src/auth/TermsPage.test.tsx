import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import type { SessionInfo } from "../api/auth";
import { createClient } from "../api/client";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { ToastProvider } from "../components/toast/ToastProvider";
import { createI18n } from "../i18n";
import { createTokenStorage } from "./tokenStorage";
import { TermsPage } from "./TermsPage";

const PENDING_SESSION: SessionInfo = {
  user: { email: "ana@empresa.com", name: "Ana" },
  terms_status: "not_accepted",
  terms: { version: "2.0", locale: "es", content: "Texto **obligatorio** de términos." },
};

const NO_VERSION_SESSION: SessionInfo = {
  user: { email: "ana@empresa.com", name: "Ana" },
  terms_status: "no_current_version",
  terms: null,
};

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderTerms(
  session: SessionInfo,
  fetcher: typeof fetch,
  callbacks: { onAccepted?: () => void; onLoggedOut?: () => void } = {},
) {
  const i18n = createI18n("es");
  const storage = createTokenStorage(null);
  storage.set("tok-terms");
  const client = createClient({
    kind: "app",
    appBaseUrl: "",
    language: () => i18n.language,
    fetch: fetcher,
    tokenStorage: storage,
  });
  render(
    <I18nextProvider i18n={i18n}>
      <LiveAnnouncer>
        <ToastProvider>
          <TermsPage
            client={client}
            session={session}
            tokenStorage={storage}
            onAccepted={callbacks.onAccepted}
            onLoggedOut={callbacks.onLoggedOut}
          />
        </ToastProvider>
      </LiveAnnouncer>
    </I18nextProvider>,
  );
  return { storage };
}

beforeEach(() => {
  window.history.pushState(null, "", "/terms");
});

test("muestra el documento en Markdown, exige marcar la casilla y navega a / al aceptar", async () => {
  const sent: { url: string; body: unknown }[] = [];
  let accepted = false;
  renderTerms(
    PENDING_SESSION,
    (url, init) => {
      sent.push({ url: String(url), body: JSON.parse(String(init?.body ?? "{}")) });
      return Promise.resolve(json(200, { terms_status: "accepted" }));
    },
    { onAccepted: () => (accepted = true) },
  );

  await userEvent.click(screen.getByRole("link", { name: "Acepto los términos y condiciones" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("Texto obligatorio de términos.");
  await userEvent.click(screen.getByRole("button", { name: "Cerrar" }));

  await userEvent.click(screen.getByRole("button", { name: "Aceptar y continuar" }));
  expect(screen.getByText("Debes aceptar los términos y condiciones.")).toBeInTheDocument();
  expect(sent).toEqual([]);

  await userEvent.click(
    screen.getByRole("checkbox", { name: "Acepto los términos y condiciones" }),
  );
  await userEvent.click(screen.getByRole("button", { name: "Aceptar y continuar" }));

  expect(sent).toEqual([
    {
      url: "/api/app/v1/auth/terms/accept",
      body: { version: "2.0", locale: "es", accepted: true, language: "es" },
    },
  ]);
  expect(accepted).toBe(true);
  expect(window.location.pathname).toBe("/");
});

test("muestra error cuando los términos cambiaron y cierra sesión incluso si falla la red", async () => {
  let loggedOut = false;
  const { storage } = renderTerms(
    PENDING_SESSION,
    (url) => {
      if (String(url).endsWith("/terms/accept")) {
        return Promise.resolve(
          json(400, {
            errors: { non_field_errors: [{ code: "not_current_document", message: "x" }] },
          }),
        );
      }
      return Promise.reject(new TypeError("offline"));
    },
    { onLoggedOut: () => (loggedOut = true) },
  );

  await userEvent.click(
    screen.getByRole("checkbox", { name: "Acepto los términos y condiciones" }),
  );
  await userEvent.click(screen.getByRole("button", { name: "Aceptar y continuar" }));
  expect(
    await screen.findByText(/Los términos han cambiado\. Revísalos y acéptalos de nuevo\./),
  ).toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
  expect(storage.get()).toBeNull();
  expect(loggedOut).toBe(true);
  expect(window.location.pathname).toBe("/login");
});

test("oculta el formulario y permite cerrar sesión cuando no hay versión vigente publicada", async () => {
  let loggedOut = false;
  const { storage } = renderTerms(
    NO_VERSION_SESSION,
    () => Promise.resolve(json(401, { code: "unauthenticated", message: "x" })),
    { onLoggedOut: () => (loggedOut = true) },
  );

  expect(
    screen.getByText(
      /No es posible continuar en este momento porque no hay una versión de términos vigente\./,
    ),
  ).toBeInTheDocument();
  expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Aceptar y continuar" })).not.toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
  expect(storage.get()).toBeNull();
  expect(loggedOut).toBe(true);
  expect(window.location.pathname).toBe("/login");
});
