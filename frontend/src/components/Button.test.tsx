import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactElement } from "react";
import { I18nextProvider } from "react-i18next";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";

import { createI18n } from "../i18n";
import { AnnouncerContext } from "./announcer";
import { Button } from "./Button";

function renderInSpanish(element: ReactElement, announce = vi.fn()) {
  const view = render(
    <I18nextProvider i18n={createI18n("es")}>
      <AnnouncerContext.Provider value={announce}>{element}</AnnouncerContext.Provider>
    </I18nextProvider>,
  );
  const rerender = (next: ReactElement) =>
    view.rerender(
      <I18nextProvider i18n={createI18n("es")}>
        <AnnouncerContext.Provider value={announce}>{next}</AnnouncerContext.Provider>
      </I18nextProvider>,
    );
  return { rerender, announce };
}

test("its accessible name is its visible text", () => {
  render(<Button>Verify</Button>);

  expect(screen.getByRole("button", { name: "Verify" })).toHaveTextContent("Verify");
});

test("is a plain button unless told to submit", () => {
  render(
    <>
      <Button>Plain</Button>
      <Button type="submit">Send</Button>
    </>,
  );

  expect(screen.getByRole("button", { name: "Plain" })).toHaveAttribute("type", "button");
  expect(screen.getByRole("button", { name: "Send" })).toHaveAttribute("type", "submit");
});

test("is activated by click, Enter and Space", async () => {
  const user = userEvent.setup();
  const onClick = vi.fn();
  render(<Button onClick={onClick}>Verify</Button>);

  await user.click(screen.getByRole("button", { name: "Verify" }));
  await user.keyboard("{Enter}");
  await user.keyboard(" ");

  expect(onClick).toHaveBeenCalledTimes(3);
});

test("with keepFocusOnMouseDown, pressing it with the mouse leaves the focus where it was", async () => {
  const user = userEvent.setup();
  const onClick = vi.fn();
  render(
    <>
      <input aria-label="Field" />
      <Button keepFocusOnMouseDown onClick={onClick}>
        Verify
      </Button>
    </>,
  );

  const field = screen.getByRole("textbox", { name: "Field" });
  await user.click(field);
  await user.click(screen.getByRole("button", { name: "Verify" }));

  expect(field).toHaveFocus();
  expect(onClick).toHaveBeenCalledTimes(1);
  expect(fireEvent.mouseDown(screen.getByRole("button", { name: "Verify" }))).toBe(false);
});

test("without keepFocusOnMouseDown, the mouse moves the focus to the button", () => {
  render(<Button>Verify</Button>);

  expect(fireEvent.mouseDown(screen.getByRole("button", { name: "Verify" }))).toBe(true);
});

test("keepFocusOnMouseDown does not change the keyboard", async () => {
  const user = userEvent.setup();
  const onClick = vi.fn();
  render(
    <Button keepFocusOnMouseDown onClick={onClick}>
      Verify
    </Button>,
  );

  await user.tab();
  expect(screen.getByRole("button", { name: "Verify" })).toHaveFocus();
  await user.keyboard("{Enter}");

  expect(onClick).toHaveBeenCalledTimes(1);
});

test("still calls its own onMouseDown when keeping the focus", () => {
  const onMouseDown = vi.fn();
  render(
    <Button keepFocusOnMouseDown onMouseDown={onMouseDown}>
      Verify
    </Button>,
  );

  fireEvent.mouseDown(screen.getByRole("button", { name: "Verify" }));

  expect(onMouseDown).toHaveBeenCalledTimes(1);
});

test("while processing, it says so in its text and name and is marked as disabled", () => {
  renderInSpanish(<Button processing>Verificar</Button>);

  const button = screen.getByRole("button", { name: "Procesando…" });
  expect(button).toHaveTextContent("Procesando…");
  expect(button).toHaveAttribute("aria-disabled", "true");
  expect(button).not.toBeDisabled();
});

test("while processing, clicks, Enter and Space are ignored and the focus stays", async () => {
  const user = userEvent.setup();
  const onClick = vi.fn();
  renderInSpanish(
    <Button processing onClick={onClick}>
      Verificar
    </Button>,
  );

  await user.tab();
  const button = screen.getByRole("button", { name: "Procesando…" });
  expect(button).toHaveFocus();
  await user.click(button);
  await user.keyboard("{Enter}");
  await user.keyboard(" ");

  expect(onClick).not.toHaveBeenCalled();
  expect(button).toHaveFocus();
});

test("while processing, a submit button does not submit its form", async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn((event: React.FormEvent) => event.preventDefault());
  renderInSpanish(
    <form onSubmit={onSubmit}>
      <input aria-label="Field" />
      <Button type="submit" processing>
        Verificar
      </Button>
    </form>,
  );

  await user.type(screen.getByRole("textbox", { name: "Field" }), "x{Enter}");
  await user.click(screen.getByRole("button", { name: "Procesando…" }));

  expect(onSubmit).not.toHaveBeenCalled();
});

test("entering the processing state is announced once, leaving it is not", () => {
  const { rerender, announce } = renderInSpanish(<Button>Verificar</Button>);
  expect(announce).not.toHaveBeenCalled();

  rerender(<Button processing>Verificar</Button>);
  expect(announce).toHaveBeenCalledTimes(1);
  expect(announce).toHaveBeenCalledWith("Procesando", "polite");

  rerender(<Button>Verificar</Button>);
  expect(screen.getByRole("button", { name: "Verificar" })).not.toHaveAttribute("aria-disabled");
  expect(announce).toHaveBeenCalledTimes(1);
});

test("is a primary button by default, marked for the design system", () => {
  render(<Button>Save</Button>);

  const button = screen.getByRole("button", { name: "Save" });
  expect(button).toHaveClass("btn", "btn-primary");
  expect(button).not.toHaveClass("btn-ghost", "hov");
  expect(button).toHaveAttribute("data-ui", "button-primary");
});

test("the secondary variant is an outlined button with the hover of the design system", () => {
  render(<Button variant="secondary">Cancel</Button>);

  const button = screen.getByRole("button", { name: "Cancel" });
  expect(button).toHaveClass("btn", "btn-ghost", "hov");
  expect(button).not.toHaveClass("btn-primary");
  expect(button).toHaveAttribute("data-ui", "button-secondary");
});

test("extra class names and attributes reach the button, but not over the variant", () => {
  render(
    <Button className="wide" id="b1" variant="secondary">
      Cancel
    </Button>,
  );

  const button = screen.getByRole("button", { name: "Cancel" });
  expect(button).toHaveClass("btn", "btn-ghost", "wide");
  expect(button).toHaveAttribute("id", "b1");
});

test("the processing state keeps the variant", () => {
  renderInSpanish(
    <Button variant="secondary" processing>
      Cancelar
    </Button>,
  );

  expect(screen.getByRole("button", { name: "Procesando…" })).toHaveClass("btn-ghost");
});

test("has no accessibility violations in either variant or while processing", async () => {
  const { container } = render(
    <div>
      <Button>One</Button>
      <Button variant="secondary">Two</Button>
      <Button processing>Three</Button>
    </div>,
  );
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
