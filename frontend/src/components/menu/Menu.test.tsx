import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";

import { Menu, type MenuOption } from "./Menu";

const OPTIONS: MenuOption[] = [
  { value: "es", label: "Español", lang: "es" },
  { value: "pt", label: "Português", lang: "pt" },
  { value: "en", label: "English", lang: "en" },
];

function renderMenu(overrides: Partial<React.ComponentProps<typeof Menu>> = {}) {
  const onSelect = vi.fn();
  const view = render(
    <div>
      <button type="button">before</button>
      <Menu
        label="Language"
        options={OPTIONS}
        value="pt"
        onSelect={onSelect}
        renderTrigger={(props) => (
          <button {...props} aria-label="Language">
            Choose
          </button>
        )}
        {...overrides}
      />
      <button type="button">after</button>
    </div>,
  );
  const trigger = screen.getByRole("combobox");
  return { ...view, onSelect, trigger };
}

test("starts closed, with a trigger that announces a listbox popup", () => {
  const { trigger } = renderMenu();

  expect(trigger).toHaveAttribute("aria-haspopup", "listbox");
  expect(trigger).toHaveAttribute("aria-expanded", "false");
  expect(trigger).not.toHaveAttribute("aria-activedescendant");
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
});

test("a click opens a named listbox with the options, the selected one marked and highlighted", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenu();

  await user.click(trigger);

  const listbox = screen.getByRole("listbox", { name: "Language" });
  expect(trigger).toHaveAttribute("aria-expanded", "true");
  expect(trigger).toHaveAttribute("aria-controls", listbox.id);
  const options = screen.getAllByRole("option");
  expect(options.map((option) => option.textContent)).toEqual(["Español", "Português", "English"]);
  expect(options[1]).toHaveAttribute("aria-selected", "true");
  expect(options[0]).toHaveAttribute("aria-selected", "false");
  expect(trigger).toHaveAttribute("aria-activedescendant", options[1].id);
  expect(options[1]).toHaveClass("highlight");
  expect(options[0]).toHaveAttribute("lang", "es");
  expect(trigger).toHaveFocus();
});

test("opens with the keyboard", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenu();

  trigger.focus();
  for (const key of ["{ArrowDown}", "{Enter}", " ", "{ArrowUp}"]) {
    await user.keyboard(key);
    expect(screen.getByRole("listbox")).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  }
});

test("the highlight moves with the arrows, Home and End and stops at the ends", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenu();
  trigger.focus();
  await user.keyboard("{ArrowDown}");
  const options = screen.getAllByRole("option");
  const highlighted = () => trigger.getAttribute("aria-activedescendant");

  await user.keyboard("{ArrowDown}");
  expect(highlighted()).toBe(options[2].id);
  await user.keyboard("{ArrowDown}");
  expect(highlighted()).toBe(options[2].id);
  await user.keyboard("{Home}");
  expect(highlighted()).toBe(options[0].id);
  await user.keyboard("{ArrowUp}");
  expect(highlighted()).toBe(options[0].id);
  await user.keyboard("{End}");
  expect(highlighted()).toBe(options[2].id);
  expect(options[2]).toHaveClass("highlight");
  expect(options[1]).not.toHaveClass("highlight");
});

test("Enter or Space chooses the highlighted option, closes and keeps the focus on the trigger", async () => {
  const user = userEvent.setup();
  const { trigger, onSelect } = renderMenu();
  trigger.focus();

  await user.keyboard("{ArrowDown}{ArrowDown}{Enter}");
  expect(onSelect).toHaveBeenLastCalledWith("en");
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();

  await user.keyboard("{ArrowDown}{Home} ");
  expect(onSelect).toHaveBeenLastCalledWith("es");
  expect(onSelect).toHaveBeenCalledTimes(2);
});

test("a click on an option chooses it without taking the focus from the trigger", async () => {
  const user = userEvent.setup();
  const { trigger, onSelect } = renderMenu();
  await user.click(trigger);

  await user.click(screen.getByRole("option", { name: "English" }));

  expect(onSelect).toHaveBeenCalledWith("en");
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});

test("hovering an option highlights it", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenu();
  await user.click(trigger);

  const first = screen.getByRole("option", { name: "Español" });
  await user.hover(first);

  expect(trigger).toHaveAttribute("aria-activedescendant", first.id);
});

test("Escape closes without choosing and returns the focus to the trigger", async () => {
  const user = userEvent.setup();
  const { trigger, onSelect } = renderMenu();
  await user.click(trigger);
  screen.getByRole("option", { name: "Español" }).focus();

  await user.keyboard("{Escape}");

  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  expect(onSelect).not.toHaveBeenCalled();
  expect(trigger).toHaveFocus();
});

test("a click outside or tabbing away closes it", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenu();

  await user.click(trigger);
  await user.click(screen.getByRole("button", { name: "after" }));
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();

  await user.click(trigger);
  await user.tab();
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
});

test("clicking the trigger again closes it", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenu();
  await user.click(trigger);
  await user.click(trigger);
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
});

test("opens animated after the first frame and closes without animation", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenu();
  await user.click(trigger);

  const listbox = screen.getByRole("listbox");
  await waitFor(() => expect(listbox).toHaveClass("open"));

  await user.keyboard("{Escape}");
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
});

test("without a selected value it highlights the first option", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenu({ value: undefined });
  await user.click(trigger);

  expect(trigger).toHaveAttribute("aria-activedescendant", screen.getAllByRole("option")[0].id);
  expect(
    screen.getAllByRole("option").some((option) => option.getAttribute("aria-selected") === "true"),
  ).toBe(false);
});

test("the listbox can be aligned to the right of the trigger", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenu({ align: "right" });
  await user.click(trigger);
  expect(screen.getByRole("listbox")).toHaveClass("menu-right");
});

test("ignores the keyboard when there are no options", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenu({ options: [] });
  trigger.focus();
  await user.keyboard("{ArrowDown}");
  expect(screen.getByRole("listbox")).toBeInTheDocument();
  await user.keyboard("{Enter}");
  expect(trigger).not.toHaveAttribute("aria-activedescendant");
});

test("has no accessibility violations open and closed", async () => {
  const user = userEvent.setup();
  const { container, trigger } = renderMenu();
  const run = () => axe.run(container, { rules: { "color-contrast": { enabled: false } } });

  expect((await run()).violations).toEqual([]);
  await user.click(trigger);
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 30));
  });
  expect((await run()).violations).toEqual([]);
});

test("the wrapper does not close the menu when pointer events start inside it", () => {
  const { trigger } = renderMenu();
  fireEvent.click(trigger);
  fireEvent.mouseDown(screen.getByRole("listbox"));
  expect(screen.getByRole("listbox")).toBeInTheDocument();
});

test("a press outside closes it even when the trigger never received the focus", () => {
  const { trigger } = renderMenu();
  fireEvent.click(trigger);
  expect(screen.getByRole("listbox")).toBeInTheDocument();

  fireEvent.mouseDown(document.body);

  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
});

test("releasing the space bar does not click the trigger again, which would close what it just opened", () => {
  const { trigger } = renderMenu();

  expect(fireEvent.keyUp(trigger, { key: " " })).toBe(false);
  expect(fireEvent.keyUp(trigger, { key: "a" })).toBe(true);
});
