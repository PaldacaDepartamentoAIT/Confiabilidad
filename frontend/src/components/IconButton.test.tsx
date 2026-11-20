import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import type { ReactElement } from "react";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { IconLogOut } from "../icons";
import { AnnouncerContext } from "./announcer";
import { IconButton } from "./IconButton";
import css from "./IconButton.css?raw";

function renderInSpanish(element: ReactElement, announce = vi.fn()) {
  const view = render(
    <I18nextProvider i18n={createI18n("es")}>
      <AnnouncerContext.Provider value={announce}>{element}</AnnouncerContext.Provider>
    </I18nextProvider>,
  );
  return { ...view, announce };
}

test("exposes its label as accessible name and upward tooltip text", () => {
  const { container } = renderInSpanish(<IconButton label="Cerrar sesión" icon={<IconLogOut />} />);

  const button = screen.getByRole("button", { name: "Cerrar sesión" });
  expect(button).toHaveAttribute("type", "button");
  expect(button).toHaveAttribute("data-ui", "icon-button");
  expect(button).toHaveClass("icon-btn", "hov");
  expect(button.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  const tip = container.querySelector(".icon-btn-tip");
  expect(tip).toHaveTextContent("Cerrar sesión");
  expect(tip).toHaveAttribute("aria-hidden", "true");
});

test("responds to click, Enter and Space", async () => {
  const user = userEvent.setup();
  const onClick = vi.fn();
  renderInSpanish(<IconButton label="Cerrar sesión" icon={<IconLogOut />} onClick={onClick} />);

  const button = screen.getByRole("button", { name: "Cerrar sesión" });
  await user.click(button);
  await user.keyboard("{Enter}");
  await user.keyboard(" ");

  expect(onClick).toHaveBeenCalledTimes(3);
});

test("keeps focus when keepFocusOnMouseDown is enabled", async () => {
  const user = userEvent.setup();
  renderInSpanish(
    <>
      <input aria-label="Campo" />
      <IconButton label="Cerrar sesión" icon={<IconLogOut />} keepFocusOnMouseDown />
    </>,
  );

  const field = screen.getByRole("textbox", { name: "Campo" });
  await user.click(field);
  await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));

  expect(field).toHaveFocus();
  expect(fireEvent.mouseDown(screen.getByRole("button", { name: "Cerrar sesión" }))).toBe(false);
});

test("while processing, announces once, updates label and ignores clicks", async () => {
  const user = userEvent.setup();
  const onClick = vi.fn();
  const { rerender, announce, container } = renderInSpanish(
    <IconButton label="Cerrar sesión" icon={<IconLogOut />} onClick={onClick} />,
  );

  rerender(
    <I18nextProvider i18n={createI18n("es")}>
      <AnnouncerContext.Provider value={announce}>
        <IconButton label="Cerrar sesión" icon={<IconLogOut />} processing onClick={onClick} />
      </AnnouncerContext.Provider>
    </I18nextProvider>,
  );

  const button = screen.getByRole("button", { name: "Procesando…" });
  expect(button).toHaveAttribute("aria-disabled", "true");
  expect(container.querySelector(".icon-btn-tip")).toHaveTextContent("Procesando…");
  expect(announce).toHaveBeenCalledWith("Procesando, por favor espera.", "polite");

  await user.click(button);
  expect(onClick).not.toHaveBeenCalled();
});

test("defines bordered icon button rules and upward hover tooltip in css", () => {
  expect(css).toMatch(/border:\s*1px solid var\(--primary\)/);
  expect(css).toMatch(/bottom:\s*calc\(100% \+ 6px\)/);
  expect(css).toMatch(/\.icon-btn:hover \+ \.icon-btn-tip/);
});

test("has no accessibility violations", async () => {
  const { container } = renderInSpanish(<IconButton label="Cerrar sesión" icon={<IconLogOut />} />);
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
