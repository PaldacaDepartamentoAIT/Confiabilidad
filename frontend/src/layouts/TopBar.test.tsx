import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { useState } from "react";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { IconHouse } from "../icons";
import { AppLayout } from "./AppLayout";
import { tabPanelId } from "./tabIds";
import { TopBar } from "./TopBar";

const TABS = [
  { id: "summary", label: "Resumen" },
  { id: "inventory", label: "Inventario" },
];

function Screen() {
  const [active, setActive] = useState("summary");
  return (
    <I18nextProvider i18n={createI18n("es")}>
      <AppLayout
        items={[{ id: "home", label: "Inicio", href: "#", icon: <IconHouse /> }]}
        topBar={
          <TopBar
            tabsLabel="Secciones de la pantalla"
            tabs={TABS}
            activeId={active}
            onChange={setActive}
            searchLabel="Buscar"
            searchPlaceholder="Buscar…"
          />
        }
      >
        {TABS.map((tab) => (
          <div
            key={tab.id}
            role="tabpanel"
            id={tabPanelId("tabs", tab.id)}
            aria-labelledby={`tabs-tab-${tab.id}`}
            hidden={tab.id !== active}
          >
            content
          </div>
        ))}
      </AppLayout>
    </I18nextProvider>
  );
}

beforeEach(() => {
  vi.stubGlobal("matchMedia", () => ({
    matches: false,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
  document.documentElement.removeAttribute("data-theme");
});

test("puts the tabs on the left of the top bar and the search on the right", () => {
  render(<Screen />);

  const bar = screen.getByRole("banner");
  const area = bar.querySelector(".tabs-area");
  const search = bar.querySelector(".search");
  expect(area).toBeInTheDocument();
  expect(search).toBeInTheDocument();
  expect(
    (area as HTMLElement).compareDocumentPosition(search as HTMLElement) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(bar.lastElementChild).toBe(search);
  expect(
    within(area as HTMLElement).getByRole("tablist", { name: "Secciones de la pantalla" }),
  ).toBeInTheDocument();
  expect(
    within(search as HTMLElement).getByRole("searchbox", { name: "Buscar" }),
  ).toBeInTheDocument();
});

test("the tabs sit in a clipped area that takes the room the search leaves", () => {
  render(<Screen />);

  const area = screen.getByRole("banner").querySelector(".tabs-area");
  expect(area?.firstElementChild).toHaveClass("tabs-clip");
  expect(area?.firstElementChild?.firstElementChild).toHaveClass("tablist");
});

test("choosing a tab changes the active one", async () => {
  const user = userEvent.setup();
  render(<Screen />);

  await user.click(screen.getByRole("tab", { name: "Inventario" }));

  expect(screen.getByRole("tab", { name: "Inventario" })).toHaveAttribute("aria-selected", "true");
  expect(screen.getByRole("tab", { name: "Resumen" })).toHaveAttribute("aria-selected", "false");
});

test("has no accessibility violations", async () => {
  const { container } = render(<Screen />);
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});

test("the prefix of the tab and panel ids can be chosen", () => {
  render(
    <TopBar
      tabsLabel="Secciones"
      tabs={TABS}
      activeId="summary"
      onChange={() => undefined}
      idPrefix="assets"
      searchLabel="Buscar"
      searchPlaceholder="Buscar…"
    />,
  );

  const tab = screen.getByRole("tab", { name: "Resumen" });
  expect(tab).toHaveAttribute("id", "assets-tab-summary");
  expect(tab).toHaveAttribute("aria-controls", "assets-panel-summary");
});
