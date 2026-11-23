import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import type { ReactElement } from "react";
import { I18nextProvider } from "react-i18next";

import type { ActiveSessionItem, SessionInfo } from "../api/auth";
import { createClient } from "../api/client";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { createI18n } from "../i18n";
import { HomePage } from "./HomePage";
import { LoginPage } from "./LoginPage";
import { TermsPage } from "./TermsPage";
import { createTokenStorage } from "./tokenStorage";

const USER = { email: "ana@empresa.com", name: "Ana García" };
const ACCEPTED: SessionInfo = { user: USER, terms_status: "accepted", terms: null };
const PENDING: SessionInfo = {
  user: USER,
  terms_status: "not_accepted",
  terms: { version: "1", locale: "es", content: "Términos vigentes." },
};
const NO_TERMS: SessionInfo = { user: USER, terms_status: "no_current_version", terms: null };

const ONE_SESSION: ActiveSessionItem[] = [
  {
    id: 1,
    ip: "192.0.2.1",
    user_agent: "Chrome/130",
    created_at: "2026-11-19T10:00:00Z",
    last_seen_at: "2026-11-19T12:00:00Z",
    is_current: true,
  },
];
const MANY_SESSIONS: ActiveSessionItem[] = [
  ...ONE_SESSION,
  { ...ONE_SESSION[0], id: 2, ip: "198.51.100.5", user_agent: "Tauri/2.0", is_current: false },
];

function makeClient(sessions: ActiveSessionItem[] = ONE_SESSION) {
  const storage = createTokenStorage(null);
  storage.set("tok-a11y");
  const fetcher: typeof fetch = () =>
    Promise.resolve(
      new Response(JSON.stringify({ sessions }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  const client = createClient({
    kind: "app",
    appBaseUrl: "",
    language: () => "es",
    fetch: fetcher,
    tokenStorage: storage,
  });
  return { client, storage };
}

function renderInEs(element: ReactElement) {
  return render(
    <I18nextProvider i18n={createI18n("es")}>
      <LiveAnnouncer>{element}</LiveAnnouncer>
    </I18nextProvider>,
  );
}

async function violationsOf() {
  const results = await axe.run(document.documentElement, {
    rules: { "color-contrast": { enabled: false } },
  });
  return results.violations.map(
    (violation) => `${violation.id}: ${violation.nodes.map((node) => node.target).join(", ")}`,
  );
}

test("LoginPage has no accessibility violations in normal or error state", async () => {
  const { client, storage } = makeClient();
  renderInEs(<LoginPage client={client} tokenStorage={storage} />);
  expect(await violationsOf()).toEqual([]);

  await userEvent.setup().click(screen.getByRole("button", { name: "Iniciar sesión" }));
  expect(document.querySelector('[aria-invalid="true"]')).not.toBeNull();
  expect(await violationsOf()).toEqual([]);
}, 15_000);

test("TermsPage has no accessibility violations with pending terms or no current version", async () => {
  const { client, storage } = makeClient();
  const { rerender } = renderInEs(
    <TermsPage client={client} session={PENDING} tokenStorage={storage} />,
  );
  expect(await violationsOf()).toEqual([]);

  rerender(
    <I18nextProvider i18n={createI18n("es")}>
      <LiveAnnouncer>
        <TermsPage client={client} session={NO_TERMS} tokenStorage={storage} />
      </LiveAnnouncer>
    </I18nextProvider>,
  );
  expect(await violationsOf()).toEqual([]);
}, 15_000);

test("HomePage has no accessibility violations with one or multiple sessions", async () => {
  const one = makeClient(ONE_SESSION);
  const view = renderInEs(
    <HomePage client={one.client} session={ACCEPTED} tokenStorage={one.storage} />,
  );
  expect(await screen.findByText("192.0.2.1")).toBeInTheDocument();
  expect(await violationsOf()).toEqual([]);

  view.unmount();
  const many = makeClient(MANY_SESSIONS);
  renderInEs(<HomePage client={many.client} session={ACCEPTED} tokenStorage={many.storage} />);
  expect(await screen.findByText("198.51.100.5")).toBeInTheDocument();
  expect(await violationsOf()).toEqual([]);
}, 15_000);
