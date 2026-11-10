import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

test("is a named region with the system name and a toggle in its header", () => {
  renderSidebar();

  const sidebar = screen.getByRole("complementary", { name: "Menú principal" });
  expect(sidebar).toHaveAttribute("data-ui", "sidebar");
  expect(sidebar).toHaveClass("sidebar");
  expect(sidebar).not.toHaveClass("collapsed");
  const header = sidebar.querySelector(".sb-head");
  expect(header).toHaveAttribute("data-ui", "sidebar-header");
  expect(within(header as HTMLElement).getByText("Confiabilidad")).toHaveAttribute(
    "data-ui",
    "brand",
  );
  expect(
    within(header as HTMLElement).getByRole("button", { name: "Contraer menú" }),
  ).toBeInTheDocument();
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

test("the footer stacks the theme button, the language button and the user", () => {
  renderSidebar({ user: { name: "Laura Gómez", initials: "LG" } });

  const footer = document.querySelector(".sb-foot");
  const row = footer?.querySelector(".sb-row");
  expect(row?.children).toHaveLength(2);
  expect(
    within(row as HTMLElement).getByRole("button", {
      name: /^Tema (claro|oscuro)\. Cambiar tema$/,
    }),
  ).toBeInTheDocument();
  expect(
    within(row as HTMLElement).getByRole("combobox", { name: "Idioma: Español" }),
  ).toBeInTheDocument();
  expect(footer?.lastElementChild).toHaveClass("user-btn");
});

test("the user is a button when it has an action and plain information when it does not", async () => {
  const user = userEvent.setup();
  const onClick = vi.fn();
  const { rerender } = renderSidebar({ user: { name: "Laura Gómez", initials: "LG", onClick } });

  const button = screen.getByRole("button", { name: "Laura Gómez" });
  expect(button).toHaveClass("sb-btn", "user-btn");
  expect(button.querySelector(".avatar")).toHaveTextContent("LG");
  expect(button.querySelector(".avatar")).toHaveAttribute("data-ui", "avatar");
  expect(button.querySelector(".avatar")).toHaveAttribute("aria-hidden", "true");
  await user.click(button);
  expect(onClick).toHaveBeenCalledTimes(1);

  rerender(
    <I18nextProvider i18n={createI18n("es")}>
      <Sidebar items={ITEMS} activeId="work" user={{ name: "Laura Gómez", initials: "LG" }} />
    </I18nextProvider>,
  );
  expect(screen.queryByRole("button", { name: "Laura Gómez" })).not.toBeInTheDocument();
  expect(screen.getByText("Laura Gómez").closest(".user-btn")).toBeInTheDocument();
});

test("without a user there is no user row", () => {
  renderSidebar();
  expect(document.querySelector(".user-btn")).not.toBeInTheDocument();
});

test("the toggle collapses and expands the menu, naming its state and showing titles when narrow", async () => {
  const user = userEvent.setup();
  renderSidebar();
  const sidebar = screen.getByRole("complementary");
  const toggle = screen.getByRole("button", { name: "Contraer menú" });
  expect(toggle).toHaveAttribute("aria-expanded", "true");
  expect(toggle).toHaveAttribute("aria-controls", sidebar.id);
  expect(toggle).toHaveAttribute("data-ui", "menu-toggle");
  expect(toggle.querySelector("svg")).toHaveClass("lucide-chevron-left");
  expect(toggle.querySelector("svg")).toHaveAttribute("width", "22");
  const links = screen.getAllByRole("link");
  links.forEach((link) => expect(link).not.toHaveAttribute("title"));

  await user.click(toggle);

  expect(sidebar).toHaveClass("collapsed");
  const expand = screen.getByRole("button", { name: "Expandir menú" });
  expect(expand).toBe(toggle);
  expect(expand).toHaveAttribute("aria-expanded", "false");
  expect(expand.querySelector("svg")).toHaveClass("lucide-chevron-right");
  expect(links.map((link) => link.getAttribute("title"))).toEqual([
    "Inicio",
    "Mantenimiento",
    "Alarmas",
  ]);
  expect(expand).toHaveFocus();

  await user.keyboard("{Enter}");

  expect(sidebar).not.toHaveClass("collapsed");
  expect(screen.getByRole("button", { name: "Contraer menú" })).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  links.forEach((link) => expect(link).not.toHaveAttribute("title"));
});

test("can start collapsed", () => {
  renderSidebar({ defaultCollapsed: true });
  expect(screen.getByRole("complementary")).toHaveClass("collapsed");
  expect(screen.getByRole("button", { name: "Expandir menú" })).toHaveAttribute(
    "aria-expanded",
    "false",
  );
});

test("the texts follow the language", () => {
  renderSidebar({}, "en");
  expect(screen.getByRole("complementary", { name: "Main menu" })).toBeInTheDocument();
  expect(screen.getByRole("navigation", { name: "Sections" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Collapse menu" })).toBeInTheDocument();
});

test("has no accessibility violations expanded, collapsed and with a user", async () => {
  const user = userEvent.setup();
  const { container } = renderSidebar({
    user: { name: "Laura Gómez", initials: "LG", onClick: () => undefined },
  });
  const run = () => axe.run(container, { rules: { "color-contrast": { enabled: false } } });

  expect((await run()).violations).toEqual([]);
  await user.click(screen.getByRole("button", { name: "Contraer menú" }));
  expect((await run()).violations).toEqual([]);
});
