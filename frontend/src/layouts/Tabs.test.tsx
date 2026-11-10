import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { useState } from "react";

import { tabId, tabPanelId } from "./tabIds";
import { Tabs, type TabItem } from "./Tabs";

const TABS: TabItem[] = [
  { id: "general", label: "Datos generales" },
  { id: "location", label: "Ubicación" },
  { id: "contact", label: "Contacto" },
  { id: "settings", label: "Configuración" },
];

// jsdom no calcula el diseño: cada pestaña mide su número de letras × 10 y se coloca tras las anteriores.
function stubLayout() {
  const widthOf = (element: HTMLElement) => ((element.textContent ?? "").length || 0) * 10;
  const isTab = (element: HTMLElement) => element.getAttribute("role") === "tab";
  vi.spyOn(HTMLElement.prototype, "offsetWidth", "get").mockImplementation(function (
    this: HTMLElement,
  ) {
    return isTab(this) ? widthOf(this) : 0;
  });
  vi.spyOn(HTMLElement.prototype, "offsetLeft", "get").mockImplementation(function (
    this: HTMLElement,
  ) {
    if (!isTab(this)) return 0;
    let left = 0;
    let previous = this.previousElementSibling as HTMLElement | null;
    while (previous) {
      if (isTab(previous)) left += widthOf(previous) + 4;
      previous = previous.previousElementSibling as HTMLElement | null;
    }
    return left;
  });
}

function Harness({
  onChange,
  initial = "general",
}: {
  onChange?: (id: string) => void;
  initial?: string;
}) {
  const [active, setActive] = useState(initial);
  return (
    <>
      <Tabs
        label="Secciones del formulario"
        tabs={TABS}
        activeId={active}
        idPrefix="form"
        onChange={(id) => {
          setActive(id);
          onChange?.(id);
        }}
      />
      {TABS.map((tab) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={tabPanelId("form", tab.id)}
          aria-labelledby={`form-tab-${tab.id}`}
          hidden={tab.id !== active}
        />
      ))}
    </>
  );
}

beforeEach(() => stubLayout());
afterEach(() => vi.restoreAllMocks());

test("is a named tablist whose tabs are buttons, the active one selected and the only one in the tab order", () => {
  render(<Harness />);

  const list = screen.getByRole("tablist", { name: "Secciones del formulario" });
  expect(list).toHaveClass("tablist");
  const tabs = screen.getAllByRole("tab");
  expect(tabs.map((tab) => tab.textContent)).toEqual(TABS.map((tab) => tab.label));
  tabs.forEach((tab) => {
    expect(tab).toHaveClass("tab", "hov");
    expect(tab.tagName).toBe("BUTTON");
    expect(tab).toHaveAttribute("type", "button");
  });
  expect(tabs[0]).toHaveAttribute("aria-selected", "true");
  expect(tabs[0]).toHaveAttribute("tabindex", "0");
  expect(tabs[0]).toHaveAttribute("data-ui", "tab-active");
  expect(tabs[1]).toHaveAttribute("aria-selected", "false");
  expect(tabs[1]).toHaveAttribute("tabindex", "-1");
  expect(tabs[1]).toHaveAttribute("data-ui", "tab");
});

test("each tab points at its panel with an id the panels can use", () => {
  render(<Harness />);

  const tabs = screen.getAllByRole("tab");
  expect(tabs[1]).toHaveAttribute("id", "form-tab-location");
  expect(tabs[1]).toHaveAttribute("aria-controls", "form-panel-location");
  expect(tabPanelId("form", "location")).toBe("form-panel-location");
  expect(tabId("form", "location")).toBe("form-tab-location");
});

test("a click selects a tab", async () => {
  const user = userEvent.setup();
  const onChange = vi.fn();
  render(<Harness onChange={onChange} />);

  await user.click(screen.getByRole("tab", { name: "Contacto" }));

  expect(onChange).toHaveBeenCalledWith("contact");
  expect(screen.getByRole("tab", { name: "Contacto" })).toHaveAttribute("aria-selected", "true");
  expect(screen.getByRole("tab", { name: "Datos generales" })).toHaveAttribute("tabindex", "-1");
});

test("the arrows, Home and End move the selection and the focus, and the arrows wrap around", async () => {
  const user = userEvent.setup();
  render(<Harness />);
  await user.tab();
  expect(screen.getByRole("tab", { name: "Datos generales" })).toHaveFocus();

  await user.keyboard("{ArrowRight}");
  expect(screen.getByRole("tab", { name: "Ubicación" })).toHaveFocus();
  expect(screen.getByRole("tab", { name: "Ubicación" })).toHaveAttribute("aria-selected", "true");

  await user.keyboard("{End}");
  expect(screen.getByRole("tab", { name: "Configuración" })).toHaveFocus();
  await user.keyboard("{ArrowRight}");
  expect(screen.getByRole("tab", { name: "Datos generales" })).toHaveFocus();
  await user.keyboard("{ArrowLeft}");
  expect(screen.getByRole("tab", { name: "Configuración" })).toHaveFocus();
  await user.keyboard("{Home}");
  expect(screen.getByRole("tab", { name: "Datos generales" })).toHaveFocus();
});

test("other keys do nothing", async () => {
  const user = userEvent.setup();
  const onChange = vi.fn();
  render(<Harness onChange={onChange} />);
  await user.tab();

  await user.keyboard("a{ArrowDown}");

  expect(onChange).not.toHaveBeenCalled();
});

test("a 2 px line sits under the active tab with 12 px of margin on each side", () => {
  const { container } = render(<Harness initial="location" />);

  const ink = container.querySelector(".tab-ink") as HTMLElement;
  expect(ink).toHaveAttribute("aria-hidden", "true");
  // «Ubicación» mide 9 letras = 90 px y empieza tras «Datos generales» (15 letras = 150 px) y 4 px de hueco.
  expect(ink.style.width).toBe("66px");
  expect(ink.style.transform).toBe("translateX(166px)");
});

test("the line moves to the new tab when the selection changes", async () => {
  const user = userEvent.setup();
  const { container } = render(<Harness />);
  const ink = container.querySelector(".tab-ink") as HTMLElement;
  expect(ink.style.transform).toBe("translateX(12px)");

  await user.click(screen.getByRole("tab", { name: "Contacto" }));

  // Contacto empieza tras 150 + 4 + 90 + 4 = 248 px y mide 8 letras = 80 px.
  expect(ink.style.transform).toBe("translateX(260px)");
  expect(ink.style.width).toBe("56px");
});

test("has no accessibility violations", async () => {
  const { container } = render(<Harness />);
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});

test("the keys it handles do not also scroll the page, and the others are left alone", () => {
  render(<Harness />);
  const tab = screen.getByRole("tab", { name: "Datos generales" });

  expect(fireEvent.keyDown(tab, { key: "ArrowRight" })).toBe(false);
  expect(fireEvent.keyDown(tab, { key: "Home" })).toBe(false);
  expect(fireEvent.keyDown(tab, { key: "a" })).toBe(true);
});
