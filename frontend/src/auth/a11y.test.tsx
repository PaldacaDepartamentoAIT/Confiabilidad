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

const makeSession = (terms_status: SessionInfo["terms_status"], content?: string): SessionInfo => ({
  user: { email: "ana@empresa.com", name: "Ana García" },
  terms_status,
  terms: content ? { version: "1", locale: "es", content } : null,
});
const SESSION_ITEM: ActiveSessionItem = {
  id: 1,
  ip: "192.0.2.1",
  user_agent: "Chrome/130",
  created_at: "2026-11-19T10:00:00Z",
  last_seen_at: "2026-11-19T12:00:00Z",
  is_current: true,
};

function setup(sessions: ActiveSessionItem[] = [SESSION_ITEM]) {
  const tokenStorage = createTokenStorage(null);
  tokenStorage.set("tok-a11y");
  const client = createClient({
    kind: "app",
    appBaseUrl: "",
    language: () => "es",
    fetch: () => Promise.resolve(new Response(JSON.stringify({ sessions }), { status: 200 })),
    tokenStorage,
  });
  return { client, tokenStorage };
}

const wrap = (el: ReactElement) => (
  <I18nextProvider i18n={createI18n("es")}>
    <LiveAnnouncer>{el}</LiveAnnouncer>
  </I18nextProvider>
);

async function expectClean() {
  const res = await axe.run(document.documentElement, {
    rules: { "color-contrast": { enabled: false } },
  });
  expect(res.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target).join(", ")}`)).toEqual(
    [],
  );
}

test("LoginPage has no accessibility violations in normal or error state", async () => {
  render(wrap(<LoginPage {...setup()} />));
  await expectClean();
  await userEvent.setup().click(screen.getByRole("button", { name: "Iniciar sesión" }));
  expect(document.querySelector('[aria-invalid="true"]')).not.toBeNull();
  await expectClean();
}, 15_000);

test("TermsPage has no accessibility violations with pending terms or no current version", async () => {
  const ctx = setup();
  const view = render(
    wrap(<TermsPage {...ctx} session={makeSession("not_accepted", "Términos.")} />),
  );
  await expectClean();
  view.rerender(wrap(<TermsPage {...ctx} session={makeSession("no_current_version")} />));
  await expectClean();
}, 15_000);

test("HomePage has no accessibility violations with one or multiple sessions", async () => {
  const view = render(
    wrap(<HomePage {...setup([SESSION_ITEM])} session={makeSession("accepted")} />),
  );
  expect(await screen.findByText("192.0.2.1")).toBeInTheDocument();
  await expectClean();
  view.unmount();
  const second = { ...SESSION_ITEM, id: 2, ip: "198.51.100.5", is_current: false };
  render(wrap(<HomePage {...setup([SESSION_ITEM, second])} session={makeSession("accepted")} />));
  expect(await screen.findByText("198.51.100.5")).toBeInTheDocument();
  await expectClean();
}, 15_000);
