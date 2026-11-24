import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import type { ReactElement } from "react";
import { I18nextProvider } from "react-i18next";

import type { SessionInfo } from "../api/auth";
import { createClient } from "../api/client";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { createI18n } from "../i18n";
import { HomePage } from "./HomePage";
import { LoginPage } from "./LoginPage";
import { TermsPage } from "./TermsPage";
import { createTokenStorage } from "./tokenStorage";

const info = (terms_status: SessionInfo["terms_status"], content?: string): SessionInfo => ({
  user: { email: "ana@empresa.com", name: "Ana García" },
  terms_status,
  terms: content ? { version: "1", locale: "es", content } : null,
});
const ctxFor = (ips = ["192.0.2.1"]) => {
  const tokenStorage = createTokenStorage(null);
  tokenStorage.set("tok-a11y");
  const sessions = ips.map((ip, i) => ({
    id: i + 1,
    ip,
    user_agent: "Chrome/130",
    created_at: "2026-11-19T10:00:00Z",
    last_seen_at: "2026-11-19T12:00:00Z",
    is_current: i === 0,
  }));
  const fetch = () => Promise.resolve(new Response(JSON.stringify({ sessions }), { status: 200 }));
  const client = createClient({
    kind: "app",
    appBaseUrl: "",
    language: () => "es",
    fetch,
    tokenStorage,
  });
  return { tokenStorage, client };
};
const mount = (el: ReactElement) =>
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <LiveAnnouncer>{el}</LiveAnnouncer>
    </I18nextProvider>,
  );
const check = async () => {
  const { violations } = await axe.run(document.body, {
    rules: { "color-contrast": { enabled: false } },
  });
  expect(violations.map((v) => v.id)).toEqual([]);
};

test("LoginPage, TermsPage and HomePage have no a11y violations", async () => {
  Element.prototype.scrollIntoView = () => {};
  const login = mount(<LoginPage {...ctxFor()} />);
  await check();
  await userEvent.setup().click(screen.getByRole("button", { name: "Iniciar sesión" }));
  expect(document.querySelector('[aria-invalid="true"]')).not.toBeNull();
  await check();
  login.unmount();
  delete (Element.prototype as Partial<Element>).scrollIntoView;

  const ctx = ctxFor();
  for (const el of [
    <TermsPage key="1" {...ctx} session={info("not_accepted", "Términos.")} />,
    <TermsPage key="2" {...ctx} session={info("no_current_version")} />,
  ]) {
    const v = mount(el);
    await check();
    v.unmount();
  }

  for (const [ips, text] of [
    [["192.0.2.1"], "192.0.2.1"],
    [["192.0.2.1", "198.51.100.5"], "198.51.100.5"],
  ] as const) {
    const v = mount(<HomePage {...ctxFor([...ips])} session={info("accepted")} />);
    expect(await screen.findByText(text)).toBeInTheDocument();
    await check();
    v.unmount();
  }
}, 30_000);
