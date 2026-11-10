import { render, screen, within } from "@testing-library/react";
import axe from "axe-core";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { IconBell, IconHouse, IconWrench } from "../icons";
import { Sidebar, type SidebarItem } from "./Sidebar";

const ITEMS: SidebarItem[] = [
  { id: "home", label: "Inicio", href: "#inicio", icon: <IconHouse /> },
  { id: "work", label: "Mantenimiento", href: "#mantenimiento", icon: <IconWrench /> },
  {
    id: "alarms",
    label: "Alarmas",
    href: "#alarmas",
    icon: <IconBell />,
    counter: 3,
    counterLabel: "3 sin revisar",
  },
];

function renderSidebar(props: Partial<React.ComponentProps<typeof Sidebar>> = {}, language = "es") {
  vi.stubGlobal("matchMedia", () => ({ matches: false }));
  return render(
    <I18nextProvider i18n={createI18n(language)}>
      <Sidebar items={ITEMS} activeId="work" {...props} />
    </I18nextProvider>,
  );
}

afterEach(() => {
  document.documentElement.removeAttribute("data-theme");
  vi.unstubAllGlobals();
});

test("is a named region with the system name in its header", () => {
  renderSidebar();

  const sidebar = screen.getByRole("complementary", { name: "Menú principal" });
  expect(sidebar).toHaveAttribute("data-ui", "sidebar");
  expect(sidebar).toHaveClass("sidebar");
  const header = sidebar.querySelector(".sb-head");
  expect(header).toHaveAttribute("data-ui", "sidebar-header");
  expect(within(header as HTMLElement).getByText("Confiabilidad")).toHaveAttribute(
    "data-ui",
    "brand",
  );
});

test("lists the sections as links with icon and label, marking the current one", () => {
  renderSidebar();

  const nav = screen.getByRole("navigation", { name: "Secciones" });
  const links = within(nav).getAllByRole("link");
  expect(links.map((link) => link.textContent)).toEqual(["Inicio", "Mantenimiento", "Alarmas3"]);
  expect(links.map((link) => link.getAttribute("href"))).toEqual([
    "#inicio",
    "#mantenimiento",
    "#alarmas",
  ]);
  links.forEach((link) => {
    expect(link).toHaveClass("nav-item", "hov");
    expect(link.querySelector("svg")).toBeInTheDocument();
    expect(link.querySelector(".label")).toBeInTheDocument();
  });
  expect(links[1]).toHaveAttribute("aria-current", "page");
  expect(links[1]).toHaveAttribute("data-ui", "nav-item-active");
  expect(links[0]).not.toHaveAttribute("aria-current");
  expect(links[0]).toHaveAttribute("data-ui", "nav-item");
});

test("shows a counter, with its accessible label, only on the items that have one", () => {
  renderSidebar();

  const counters = document.querySelectorAll("[data-ui='counter']");
  expect(counters).toHaveLength(1);
  expect(counters[0]).toHaveTextContent("3");
  expect(counters[0]).toHaveAttribute("aria-label", "3 sin revisar");
  expect(counters[0].closest("a")).toHaveAttribute("href", "#alarmas");
});

test("the texts follow the language", () => {
  renderSidebar({}, "en");
  expect(screen.getByRole("complementary", { name: "Main menu" })).toBeInTheDocument();
  expect(screen.getByRole("navigation", { name: "Sections" })).toBeInTheDocument();
});

test("has no accessibility violations", async () => {
  const { container } = renderSidebar();
  const run = () => axe.run(container, { rules: { "color-contrast": { enabled: false } } });

  expect((await run()).violations).toEqual([]);
});
