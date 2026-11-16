import { render, screen, within } from "@testing-library/react";
import axe from "axe-core";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { PublicLayout } from "./PublicLayout";

function renderLayout(language = "es") {
  return render(
    <I18nextProvider i18n={createI18n(language)}>
      <PublicLayout>
        <main>
          <h1>Page</h1>
        </main>
      </PublicLayout>
    </I18nextProvider>,
  );
}

afterEach(() => {
  document.documentElement.removeAttribute("data-theme");
  vi.unstubAllGlobals();
});

test("has a top bar with the system name and, on the right, the language and the theme buttons", () => {
  vi.stubGlobal("matchMedia", () => ({ matches: false }));
  renderLayout("es");

  const bar = screen.getByRole("banner");
  expect(bar).toHaveAttribute("data-ui", "topbar");
  expect(bar).toHaveClass("public-bar");
  const name = within(bar).getByText("Confiabilidad");
  expect(name).toHaveAttribute("data-ui", "brand");
  expect(name).toHaveClass("brand");
  const actions = bar.querySelector(".public-actions");
  expect(
    [...(actions?.children ?? [])].map((child) => child.getAttribute("data-ui") ?? child.className),
  ).toEqual(["select", "sidebar-button"]);
  expect(within(bar).getByRole("combobox", { name: "Idioma: Español" })).toBeInTheDocument();
  expect(
    within(bar).getByRole("button", { name: /^Tema claro\. Cambiar tema$/ }),
  ).toBeInTheDocument();
});

test("the system name follows the language", () => {
  vi.stubGlobal("matchMedia", () => ({ matches: false }));
  renderLayout("en");
  expect(within(screen.getByRole("banner")).getByText("Reliability")).toBeInTheDocument();
});

test("has no side menu and puts the page content below the bar, untouched", () => {
  vi.stubGlobal("matchMedia", () => ({ matches: false }));
  const { container } = renderLayout();

  expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  expect(container.querySelector("[data-ui='sidebar']")).not.toBeInTheDocument();
  const content = container.querySelector(".public-content");
  expect(content).toContainElement(screen.getByRole("main"));
  expect(screen.getAllByRole("main")).toHaveLength(1);
  expect(
    screen.getByRole("banner").compareDocumentPosition(screen.getByRole("main")) &
      Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
});

test("the language menu opens aligned to the right edge of the bar", async () => {
  vi.stubGlobal("matchMedia", () => ({ matches: false }));
  const { default: userEvent } = await import("@testing-library/user-event");
  renderLayout();

  await userEvent.setup().click(screen.getByRole("combobox"));

  expect(screen.getByRole("listbox")).toHaveClass("menu-right");
});

test("has no accessibility violations", async () => {
  vi.stubGlobal("matchMedia", () => ({ matches: false }));
  const { container } = renderLayout();
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
