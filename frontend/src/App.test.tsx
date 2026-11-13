import { act, render, screen, within } from "@testing-library/react";
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
  render(
    <I18nextProvider i18n={createI18n(language)}>
      <App />
    </I18nextProvider>,
  );

  expect(screen.getByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
  expect(screen.getByText(intro, { exact: false })).toBeInTheDocument();
  expect(document.documentElement.lang).toBe(language);
});

test("switches the whole page language from the keyboard and remembers it", async () => {
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
});

test.each(["/", "/ruta-que-no-existe"])("shows the sample page at %s", (path) => {
  window.history.replaceState(null, "", path);
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
};

function fakeClient() {
  const fetcher = (url: RequestInfo | URL) => {
    const route = String(url).split("?")[0].split("/").pop() ?? "";
    return Promise.resolve(new Response(JSON.stringify(answers[route] ?? {}), { status: 200 }));
  };
  return createClient({
    kind: "browser",
    appBaseUrl: "",
    language: () => "en",
    fetch: fetcher as typeof fetch,
  });
}

test.each([
  ["/register", "Create your account"],
  ["/register/continue#pid-1", "Enter the verification code"],
  ["/register/done", "Account created"],
])("shows the registration screen at %s", async (path, heading) => {
  window.history.replaceState(null, "", path);
  document.cookie = "csrftoken=token";
  render(
    <I18nextProvider i18n={createI18n("en")}>
      <App client={fakeClient()} />
    </I18nextProvider>,
  );

  expect(await screen.findByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
  window.history.replaceState(null, "", "/");
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
});

test("moving between screens does not reload the page", async () => {
  window.history.replaceState(null, "", "/register/done");
  render(
    <I18nextProvider i18n={createI18n("en")}>
      <App client={fakeClient()} />
    </I18nextProvider>,
  );

  act(() => navigate("/register"));

  expect(
    await screen.findByRole("heading", { level: 1, name: "Create your account" }),
  ).toBeVisible();
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

describe("the top bar of the registration", () => {
  afterEach(() => window.history.replaceState(null, "", "/"));

  function renderApp() {
    render(
      <I18nextProvider i18n={createI18n("en")}>
        <App client={fakeClient()} />
      </I18nextProvider>,
    );
  }

  test("there is one bar with the banner, the language and the theme", async () => {
    window.history.replaceState(null, "", "/register");
    renderApp();
    await screen.findByRole("heading", { level: 1, name: "Create your account" });

    const banners = screen.getAllByRole("banner");
    expect(banners).toHaveLength(1);
    expect(within(banners[0]).getByRole("combobox", { name: /^Language/ })).toBeInTheDocument();
    expect(within(banners[0]).getByRole("button", { name: /Switch theme/ })).toBeInTheDocument();
  });

  test("is the very same node when moving from one screen to another", async () => {
    window.history.replaceState(null, "", "/register");
    renderApp();
    await screen.findByRole("heading", { level: 1, name: "Create your account" });
    const bar = screen.getByRole("banner");
    const language = within(bar).getByRole("combobox", { name: /^Language/ });

    act(() => navigate("/register/done"));
    await screen.findByRole("heading", { level: 1, name: "Account created" });

    expect(screen.getByRole("banner")).toBe(bar);
    expect(within(bar).getByRole("combobox", { name: /^Language/ })).toBe(language);
    expect(screen.getAllByRole("banner")).toHaveLength(1);
  });

  test("the sample page keeps its own bar and the registration brings the shared one", async () => {
    window.history.replaceState(null, "", "/");
    renderApp();
    await screen.findByRole("heading", { level: 1, name: "Reliability" });
    expect(screen.getAllByRole("banner")).toHaveLength(1);

    act(() => navigate("/register/done"));
    await screen.findByRole("heading", { level: 1, name: "Account created" });
    expect(screen.getAllByRole("banner")).toHaveLength(1);
  });
});
