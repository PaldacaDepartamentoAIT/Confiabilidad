import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { App } from "./App";
import { createClient } from "./api/client";
import { createI18n } from "./i18n";
import { LANGUAGE_STORAGE_KEY, type LanguageStorage } from "./i18n/language";
import { navigate } from "./routing/router";

test.each([
  ["es", "Confiabilidad", "Vista previa de los componentes"],
  ["pt-BR", "Confiabilidade", "Prévia dos componentes"],
  ["en", "Reliability", "Preview of the shared components"],
])("renders the application in %s", (language, heading, intro) => {
  window.history.replaceState(null, "", "/showcase");
  render(
    <I18nextProvider i18n={createI18n(language)}>
      <App />
    </I18nextProvider>,
  );

  expect(screen.getByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
  expect(screen.getByText(intro, { exact: false })).toBeInTheDocument();
  expect(document.documentElement.lang).toBe(language);
  window.history.replaceState(null, "", "/");
});

test("switches the whole page language from the keyboard and remembers it", async () => {
  window.history.replaceState(null, "", "/showcase");
  const user = userEvent.setup();
  const values = new Map<string, string>();
  const storage: LanguageStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  };
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <App storage={storage} />
    </I18nextProvider>,
  );

  await user.tab();
  await user.tab();
  await user.tab();
  await user.tab();
  await user.keyboard("{Enter}");

  const portuguese = screen.getByRole("button", { name: "Português (Brasil)" });
  expect(screen.getByRole("heading", { level: 1, name: "Confiabilidade" })).toBeInTheDocument();
  expect(document.documentElement.lang).toBe("pt-BR");
  expect(document.title).toBe("Confiabilidade — Componentes");
  expect(portuguese).toHaveFocus();
  expect(storage.getItem(LANGUAGE_STORAGE_KEY)).toBe("pt-BR");
  window.history.replaceState(null, "", "/");
});

test("shows the sample page at /showcase", () => {
  window.history.replaceState(null, "", "/showcase");
  render(
    <I18nextProvider i18n={createI18n("en")}>
      <App />
    </I18nextProvider>,
  );

  expect(screen.getByRole("heading", { level: 1, name: "Reliability" })).toBeInTheDocument();
  window.history.replaceState(null, "", "/");
});

const answers: Record<string, unknown> = {
  options: {
    countries: ["ES"],
    terms: { version: "1", locale: "en", content: "T" },
    marketing: null,
  },
  status: { code_expires_in: 900, resend_in: 60, resends_left: 5, locked: false, expired: false },
  session: {
    user: { email: "ana@example.com", name: "Ana" },
    terms_status: "accepted",
    terms: null,
  },
  profile: { email: "ana@example.com", name: "Ana", birthdate: "1991-03-04", country: "ES" },
  sessions: { sessions: [] },
};

function fakeClient(
  sessionResponse: { status: number; body: unknown } = { status: 200, body: answers.session },
) {
  const fetcher = (url: RequestInfo | URL) => {
    const route = String(url).split("?")[0].split("/").pop() ?? "";
    if (route === "session") {
      return Promise.resolve(
        new Response(JSON.stringify(sessionResponse.body), { status: sessionResponse.status }),
      );
    }
    return Promise.resolve(new Response(JSON.stringify(answers[route] ?? {}), { status: 200 }));
  };
  return createClient({
    kind: "browser",
    appBaseUrl: "",
    language: () => "en",
    fetch: fetcher as typeof fetch,
  });
}

const UNAUTH = { status: 401, body: { code: "unauthenticated", message: "x" } };
const PENDING_TERMS = {
  status: 200,
  body: {
    ...(answers.session as object),
    terms_status: "not_accepted",
    terms: { version: "1", locale: "en", content: "T" },
  },
};
const renderApp = (client?: ReturnType<typeof fakeClient>) =>
  render(
    <I18nextProvider i18n={createI18n("en")}>
      <App client={client} />
    </I18nextProvider>,
  );

const ROUTE_CASES = [
  ["/", undefined, null, "Main panel"],
  ["/profile", undefined, null, "My profile"],
  ["/ruta-que-no-existe", undefined, null, "Main panel"],
  ["/showcase", undefined, null, "Reliability"],
  ["/login", UNAUTH, null, "Sign in"],
  ["/terms", PENDING_TERMS, null, "Pending terms and conditions"],
  ["/register", UNAUTH, null, "Create your account"],
  ["/register/continue#pid-1", UNAUTH, null, "Enter the verification code"],
  ["/register/done", UNAUTH, null, "Account created"],
  ["/", UNAUTH, "/login", "Sign in"],
  ["/profile", UNAUTH, "/login", "Sign in"],
  ["/terms", UNAUTH, "/login", "Sign in"],
  ["/login", undefined, "/", "Main panel"],
  ["/register", undefined, "/", "Main panel"],
  ["/login", PENDING_TERMS, "/terms", "Pending terms and conditions"],
  ["/register", PENDING_TERMS, "/terms", "Pending terms and conditions"],
  ["/", PENDING_TERMS, "/terms", "Pending terms and conditions"],
  ["/profile", PENDING_TERMS, "/terms", "Pending terms and conditions"],
  ["/terms", undefined, "/", "Main panel"],
] as const;

test.each(ROUTE_CASES)(
  "renders or redirects %s according to session and terms",
  async (from, sessionReply, target, heading) => {
    window.history.replaceState(null, "", from);
    document.cookie = "csrftoken=token";
    renderApp(fakeClient(sessionReply));
    expect(await screen.findByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
    if (target) expect(window.location.pathname).toBe(target);
    window.history.replaceState(null, "", "/");
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  },
);

test("moving between screens does not reload the page, keeps the bar and fades out then in", async () => {
  window.history.replaceState(null, "", "/register/done");
  const { container } = renderApp(fakeClient(UNAUTH));
  await screen.findByRole("heading", { level: 1, name: "Account created" });
  const barBefore = screen.getByRole("banner");
  const content = container.querySelector(".public-content");
  expect(content).not.toHaveClass("route-out", "route-in");

  act(() => navigate("/register"));
  expect(content).toHaveClass("route-out");
  expect(
    await screen.findByRole("heading", { level: 1, name: "Create your account" }),
  ).toBeVisible();
  expect(screen.getByRole("banner")).toBe(barBefore);
  expect(container.querySelector(".public-content")).toHaveClass("route-in");
  window.history.replaceState(null, "", "/");
});

test("navigates from home sidebar to /profile without reloading", async () => {
  window.history.replaceState(null, "", "/");
  renderApp(fakeClient());
  await screen.findByRole("heading", { level: 1, name: "Main panel" });
  act(() => screen.getByRole("link", { name: "Profile" }).click());
  expect(await screen.findByRole("heading", { level: 1, name: "My profile" })).toBeInTheDocument();
  expect(window.location.pathname).toBe("/profile");
  window.history.replaceState(null, "", "/");
});

test("without a given client, the screens use the one built from the environment", async () => {
  window.history.replaceState(null, "", "/register");
  const fetchSpy = vi.spyOn(window, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
  render(
    <I18nextProvider i18n={createI18n("en")}>
      <App />
    </I18nextProvider>,
  );

  expect(await screen.findByText(/Could not connect/)).toBeInTheDocument();
  expect(String(fetchSpy.mock.calls[0][0])).toBe(
    "/api/browser/v1/registration/options?language=en",
  );
  fetchSpy.mockRestore();
  window.history.replaceState(null, "", "/");
});
