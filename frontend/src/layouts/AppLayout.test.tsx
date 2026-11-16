import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { IconHouse, IconWrench } from "../icons";
import { AppLayout } from "./AppLayout";
import type { SidebarItem } from "./Sidebar";

const ITEMS: SidebarItem[] = [
  { id: "home", label: "Inicio", href: "#inicio", icon: <IconHouse /> },
  { id: "work", label: "Mantenimiento", href: "#mantenimiento", icon: <IconWrench /> },
];

function stubScreen(narrow: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query === "(max-width: 767px)" ? narrow : false,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
  }));
}

function renderLayout(props: Partial<React.ComponentProps<typeof AppLayout>> = {}) {
  return render(
    <I18nextProvider i18n={createI18n("es")}>
      <AppLayout items={ITEMS} activeId="work" {...props}>
        <h1>Page</h1>
      </AppLayout>
    </I18nextProvider>,
  );
}

afterEach(() => {
  document.documentElement.removeAttribute("data-theme");
  vi.unstubAllGlobals();
});

test("puts the side menu, the top bar and the content in the layout of the guide", () => {
  stubScreen(false);
  const { container } = renderLayout();

  const app = container.firstElementChild;
  expect(app).toHaveClass("app");
  const sidebar = screen.getByRole("complementary", { name: "Menú principal" });
  const main = container.querySelector(".main");
  expect(app?.children[0]).toBe(sidebar);
  expect(app?.children[1]).toBe(main);
  const bar = within(main as HTMLElement).getByRole("banner");
  expect(bar).toHaveAttribute("data-ui", "topbar");
  expect(bar).toHaveClass("topbar");
  const content = within(main as HTMLElement).getByRole("main");
  expect(content).toHaveAttribute("data-ui", "content");
  expect(content).toHaveClass("content");
  expect(within(content).getByRole("heading", { level: 1, name: "Page" })).toBeInTheDocument();
  expect(main?.children[0]).toBe(bar);
  expect(main?.children[1]).toBe(content);
});

test("passes the sections, the current one and the user to the side menu", () => {
  stubScreen(false);
  renderLayout({ user: { name: "Laura Gómez", initials: "LG" } });

  const sidebar = screen.getByRole("complementary");
  expect(
    within(sidebar)
      .getAllByRole("link")
      .map((link) => link.textContent),
  ).toEqual(["Inicio", "Mantenimiento"]);
  expect(within(sidebar).getByRole("link", { name: "Mantenimiento" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  expect(within(sidebar).getByText("Laura Gómez")).toBeInTheDocument();
});

test("the top bar shows what it is given after the menu button", () => {
  stubScreen(false);
  renderLayout({ topBar: <span>tabs</span> });

  const bar = screen.getByRole("banner");
  expect(bar.children[0]).toHaveClass("menu-btn");
  expect(within(bar).getByText("tabs")).toBeInTheDocument();
});

test("has a menu button in the bar that points at the side menu, closed at first", () => {
  stubScreen(true);
  renderLayout();

  const button = screen.getByRole("button", { name: "Abrir menú" });
  expect(button).toHaveClass("menu-btn", "mobile-only");
  expect(button).toHaveAttribute("aria-expanded", "false");
  expect(button).toHaveAttribute(
    "aria-controls",
    document.querySelector("[data-ui='sidebar']")?.id,
  );
  expect(button.querySelector("svg")).toHaveClass("lucide-menu");
  expect(document.querySelector("[data-ui='sidebar']")).toHaveAttribute("aria-hidden", "true");
});

test("on a narrow screen the button opens the panel and Escape closes it, returning the focus", async () => {
  stubScreen(true);
  const user = userEvent.setup();
  renderLayout();
  const button = screen.getByRole("button", { name: "Abrir menú" });
  const sidebar = document.querySelector("[data-ui='sidebar']");

  await user.click(button);

  expect(button).toHaveAttribute("aria-expanded", "true");
  expect(sidebar).toHaveClass("mobile-open");
  expect(screen.getByRole("button", { name: "Cerrar menú" })).toHaveFocus();

  await user.keyboard("{Escape}");

  expect(sidebar).not.toHaveClass("mobile-open");
  expect(button).toHaveAttribute("aria-expanded", "false");
  expect(button).toHaveFocus();
});

test("the button of the menu header closes it and returns the focus; choosing an item closes it without it", async () => {
  stubScreen(true);
  const user = userEvent.setup();
  renderLayout();
  const button = screen.getByRole("button", { name: "Abrir menú" });
  const sidebar = document.querySelector("[data-ui='sidebar']");

  await user.click(button);
  await user.click(screen.getByRole("button", { name: "Cerrar menú" }));
  expect(sidebar).not.toHaveClass("mobile-open");
  expect(button).toHaveFocus();

  await user.click(button);
  await user.click(screen.getByRole("link", { name: "Inicio" }));
  expect(sidebar).not.toHaveClass("mobile-open");
  expect(button).not.toHaveFocus();
});

test("pressing the menu button again, or outside, closes the panel", async () => {
  stubScreen(true);
  const user = userEvent.setup();
  renderLayout();
  const button = screen.getByRole("button", { name: "Abrir menú" });
  const sidebar = document.querySelector("[data-ui='sidebar']");

  await user.click(button);
  await user.click(button);
  expect(sidebar).not.toHaveClass("mobile-open");

  await user.click(button);
  await user.click(screen.getByRole("heading", { name: "Page" }));
  expect(sidebar).not.toHaveClass("mobile-open");
});

test("has no accessibility violations on a wide and on a narrow screen", async () => {
  stubScreen(false);
  const wide = renderLayout();
  expect(
    (await axe.run(wide.container, { rules: { "color-contrast": { enabled: false } } })).violations,
  ).toEqual([]);
  wide.unmount();

  stubScreen(true);
  const narrow = renderLayout();
  expect(
    (await axe.run(narrow.container, { rules: { "color-contrast": { enabled: false } } }))
      .violations,
  ).toEqual([]);
});

test("embedded, the bar and the content are plain blocks, for a page that already has its own main and banner", () => {
  stubScreen(false);
  const { container } = renderLayout({ embedded: true });

  expect(screen.queryByRole("main")).not.toBeInTheDocument();
  expect(screen.queryByRole("banner")).not.toBeInTheDocument();
  expect(container.querySelector("[data-ui='topbar']")?.tagName).toBe("DIV");
  const content = container.querySelector("[data-ui='content']");
  expect(content?.tagName).toBe("DIV");
  expect(content).toHaveClass("content");
  expect(content).toHaveTextContent("Page");
});

test("embedded, the layout is marked so that its mobile panel stays inside its own frame", () => {
  stubScreen(false);
  const embedded = renderLayout({ embedded: true });
  expect(embedded.container.firstElementChild).toHaveClass("app", "embedded");
  embedded.unmount();

  const full = renderLayout();
  expect(full.container.firstElementChild).toHaveClass("app");
  expect(full.container.firstElementChild).not.toHaveClass("embedded");
});
