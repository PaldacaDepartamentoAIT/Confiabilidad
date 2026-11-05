import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../../i18n";
import { HelpTip } from "./HelpTip";

const TEXT = "Tal como quieres que aparezca en tu cuenta.";

function renderTip() {
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <HelpTip id="tip" field="Nombre completo" description={TEXT} />
      <button type="button">Fuera</button>
    </I18nextProvider>,
  );
  return {
    button: screen.getByRole("button", { name: "Ayuda (Nombre completo)" }),
    tip: () => screen.getByText(TEXT),
  };
}

test("the button names its field, is described by the text and the text is always there", () => {
  const { button, tip } = renderTip();

  expect(button).toHaveAttribute("type", "button");
  expect(button).toHaveTextContent("?");
  expect(button).toHaveAccessibleDescription(TEXT);
  expect(tip()).toHaveAttribute("role", "tooltip");
  expect(tip()).toHaveAttribute("id", "tip");
  expect(tip()).not.toBeVisible();
});

test("the pointer over the button shows it and leaving hides it", async () => {
  const user = userEvent.setup();
  const { button, tip } = renderTip();

  await user.hover(button);
  expect(tip()).toBeVisible();

  await user.unhover(button);
  expect(tip()).not.toBeVisible();
});

test("the focus shows it, Escape and leaving hide it", async () => {
  const user = userEvent.setup();
  const { tip } = renderTip();

  await user.tab();
  expect(tip()).toBeVisible();

  await user.keyboard("{Escape}");
  expect(tip()).not.toBeVisible();

  await user.tab({ shift: true });
  await user.tab();
  expect(tip()).toBeVisible();
  await user.tab();
  expect(tip()).not.toBeVisible();
});

test("a touch shows it and another touch hides it", async () => {
  const user = userEvent.setup();
  const { button, tip } = renderTip();

  await user.pointer({ keys: "[TouchA]", target: button });
  expect(tip()).toBeVisible();

  act(() => button.focus());
  await user.pointer({ keys: "[TouchA]", target: button });
  expect(tip()).not.toBeVisible();
});

test("a mouse click does not hide what the pointer opened", async () => {
  const user = userEvent.setup();
  const { button, tip } = renderTip();

  await user.click(button);

  expect(tip()).toBeVisible();
});
