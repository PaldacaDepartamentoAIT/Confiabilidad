import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import type { ActiveSessionItem, SessionInfo } from "../api/auth";
import { createClient, type TermsStatus } from "../api/client";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { createI18n } from "../i18n";
import { HomePage } from "./HomePage";
import { createTokenStorage } from "./tokenStorage";

const SESSION: SessionInfo = {
  user: { email: "ana@empresa.com", name: "Ana García" },
  terms_status: "accepted",
  terms: null,
};

const TWO_SESSIONS: ActiveSessionItem[] = [
  {
    id: 10,
    ip: "192.0.2.10",
    user_agent: "Chrome/130",
    created_at: "2026-11-19T10:00:00Z",
    last_seen_at: "2026-11-19T12:00:00Z",
    is_current: true,
  },
  {
    id: 20,
    ip: "198.51.100.5",
    user_agent: "Tauri/2.0",
    created_at: "2026-11-18T08:00:00Z",
    last_seen_at: "2026-11-19T09:00:00Z",
    is_current: false,
  },
];

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderHome(
  fetcher: typeof fetch,
  callbacks: { onLoggedOut?: () => void; onTermsRequired?: (s: TermsStatus) => void } = {},
) {
  const i18n = createI18n("es");
  const storage = createTokenStorage(null);
  storage.set("tok-home");
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
        <HomePage
          client={client}
          session={SESSION}
          tokenStorage={storage}
          onLoggedOut={callbacks.onLoggedOut}
          onTermsRequired={callbacks.onTermsRequired}
        />
      </LiveAnnouncer>
    </I18nextProvider>,
  );
  return { storage };
}

beforeEach(() => {
  window.history.pushState(null, "", "/");
});

test("muestra usuario y sesiones activas, permite cerrar una u otras sesiones y desactiva el botón con solo una", async () => {
  renderHome((url) => {
    const path = String(url).split("?")[0];
    if (path.endsWith("/sessions")) return Promise.resolve(json(200, { sessions: TWO_SESSIONS }));
    if (path.endsWith("/sessions/revoke")) {
      return Promise.resolve(json(200, { result: "revoked" }));
    }
    return Promise.resolve(json(200, { result: "revoked", revoked_count: 1 }));
  });

  expect(await screen.findByRole("combobox", { name: "Ana García" })).toBeInTheDocument();
  expect(
    screen.queryByText("Sesión iniciada como Ana García (ana@empresa.com)"),
  ).not.toBeInTheDocument();
  expect(await screen.findByText("192.0.2.10")).toBeInTheDocument();
  expect(screen.getByText("Sesión actual")).toBeInTheDocument();

  const revokeOthers = screen.getByRole("button", { name: "Cerrar todas las demás sesiones" });
  expect(revokeOthers).toBeEnabled();

  const otherRow = screen.getByText("198.51.100.5").closest("tr");
  expect(otherRow).not.toBeNull();
  const revokeButton = within(otherRow!).getByRole("button", { name: "Cerrar sesión" });
  expect(revokeButton).toHaveAttribute("data-ui", "icon-button");
  expect(revokeButton).toHaveClass("icon-btn-sm");
  await userEvent.click(revokeButton);

  expect(screen.queryByText("198.51.100.5")).not.toBeInTheDocument();
  expect(revokeOthers).toBeDisabled();
});

test("cierra todas las demás sesiones de golpe y limpia cliente al cerrar la actual aunque falle la red", async () => {
  let loggedOut = false;
  const user = userEvent.setup();
  const { storage } = renderHome(
    (url) => {
      const path = String(url).split("?")[0];
      if (path.endsWith("/sessions")) return Promise.resolve(json(200, { sessions: TWO_SESSIONS }));
      if (path.endsWith("/sessions/revoke-others")) {
        return Promise.resolve(json(200, { result: "revoked", revoked_count: 1 }));
      }
      return Promise.reject(new TypeError("offline"));
    },
    { onLoggedOut: () => (loggedOut = true) },
  );

  expect(await screen.findByText("198.51.100.5")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Cerrar todas las demás sesiones" }));
  expect(screen.queryByText("198.51.100.5")).not.toBeInTheDocument();

  await user.click(screen.getByRole("combobox", { name: "Ana García" }));
  await user.click(screen.getByRole("option", { name: "Cerrar sesión" }));
  expect(storage.get()).toBeNull();
  expect(loggedOut).toBe(true);
  expect(window.location.pathname).toBe("/login");
});

test("redirige a /terms ante 403 terms_required y a /login ante 401 al consultar o revocar", async () => {
  const termsEvents: TermsStatus[] = [];
  renderHome(
    () =>
      Promise.resolve(
        json(403, { code: "terms_required", terms_status: "not_accepted", message: "x" }),
      ),
    { onTermsRequired: (status) => termsEvents.push(status) },
  );

  await waitFor(() => expect(window.location.pathname).toBe("/terms"));
  expect(termsEvents).toEqual(["not_accepted"]);

  window.history.pushState(null, "", "/");
  let loggedOut = false;
  renderHome(
    (url) => {
      const path = String(url).split("?")[0];
      if (path.endsWith("/sessions")) {
        return Promise.resolve(json(200, { sessions: TWO_SESSIONS }));
      }
      return Promise.resolve(json(401, { code: "unauthenticated", message: "x" }));
    },
    { onLoggedOut: () => (loggedOut = true) },
  );

  const otherRow = (await screen.findByText("198.51.100.5")).closest("tr");
  await userEvent.click(within(otherRow!).getByRole("button", { name: "Cerrar sesión" }));
  expect(loggedOut).toBe(true);
  expect(window.location.pathname).toBe("/login");
});
