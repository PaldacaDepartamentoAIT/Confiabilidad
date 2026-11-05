import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { MenuButton } from "./MenuButton";

const OPTIONS = [
  { value: "a", label: "Alfa" },
  { value: "b", label: "Beta" },
  { value: "c", label: "Gamma" },
] as const;

type Value = (typeof OPTIONS)[number]["value"];

function Menu({ name, onSelect }: { name: string; onSelect: (value: Value) => void }) {
  const [value, setValue] = useState<Value>("b");
  return (
    <MenuButton
      label={`${name}: ${value}`}
      menuLabel={name}
      options={OPTIONS}
      value={value}
      onSelect={(next) => {
        setValue(next);
        onSelect(next);
      }}
    >
      {value.toUpperCase()}
    </MenuButton>
  );
}

function renderMenus() {
  const onSelect = vi.fn();
  render(
    <>
      <Menu name="Uno" onSelect={onSelect} />
      <Menu name="Dos" onSelect={vi.fn()} />
      <button type="button">Fuera</button>
    </>,
  );
  return { onSelect, trigger: screen.getByRole("button", { name: "Uno: b" }) };
}

test("the button declares a closed menu and shows its content", () => {
  const { trigger } = renderMenus();

  expect(trigger).toHaveAttribute("type", "button");
  expect(trigger).toHaveAttribute("aria-haspopup", "menu");
  expect(trigger).toHaveAttribute("aria-expanded", "false");
  expect(trigger).toHaveTextContent("B");
  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
});

test.each(["{Enter}", " ", "{ArrowDown}"])(
  "%s opens the menu with the focus on the checked option",
  async (key) => {
    const user = userEvent.setup();
    const { trigger } = renderMenus();
    trigger.focus();

    await user.keyboard(key);

    const menu = screen.getByRole("menu", { name: "Uno" });
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(trigger).toHaveAttribute("aria-controls", menu.id);
    const items = screen.getAllByRole("menuitemradio");
    expect(items.map((item) => item.getAttribute("aria-checked"))).toEqual([
      "false",
      "true",
      "false",
    ]);
    expect(screen.getByRole("menuitemradio", { name: "Beta" })).toHaveFocus();
  },
);

test("arrows, Home and End move through the options without choosing", async () => {
  const user = userEvent.setup();
  const { trigger, onSelect } = renderMenus();
  await user.click(trigger);

  await user.keyboard("{ArrowDown}");
  expect(screen.getByRole("menuitemradio", { name: "Gamma" })).toHaveFocus();
  expect(screen.getByRole("menuitemradio", { name: "Beta" })).toHaveAttribute(
    "aria-checked",
    "true",
  );
  expect(screen.getByRole("menuitemradio", { name: "Gamma" })).toHaveAttribute(
    "aria-checked",
    "false",
  );
  await user.keyboard("{ArrowDown}");
  expect(screen.getByRole("menuitemradio", { name: "Alfa" })).toHaveFocus();
  await user.keyboard("{ArrowUp}");
  expect(screen.getByRole("menuitemradio", { name: "Gamma" })).toHaveFocus();
  await user.keyboard("{Home}");
  expect(screen.getByRole("menuitemradio", { name: "Alfa" })).toHaveFocus();
  await user.keyboard("{End}");
  expect(screen.getByRole("menuitemradio", { name: "Gamma" })).toHaveFocus();
  expect(onSelect).not.toHaveBeenCalled();
});

test.each(["{Enter}", " "])("%s chooses, closes and returns the focus", async (key) => {
  const user = userEvent.setup();
  const { onSelect } = renderMenus();
  await user.click(screen.getByRole("button", { name: "Uno: b" }));

  await user.keyboard("{ArrowDown}");
  await user.keyboard(key);

  expect(onSelect).toHaveBeenCalledWith("c");
  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  const trigger = screen.getByRole("button", { name: "Uno: c" });
  expect(trigger).toHaveAttribute("aria-expanded", "false");
  expect(trigger).toHaveFocus();
});

test("a click on an option chooses it", async () => {
  const user = userEvent.setup();
  const { trigger, onSelect } = renderMenus();
  await user.click(trigger);

  await user.click(screen.getByRole("menuitemradio", { name: "Alfa" }));

  expect(onSelect).toHaveBeenCalledWith("a");
  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Uno: a" })).toHaveFocus();
});

test("Escape closes without choosing and returns the focus to the button", async () => {
  const user = userEvent.setup();
  const { trigger, onSelect } = renderMenus();
  await user.click(trigger);
  await user.keyboard("{ArrowDown}");

  await user.keyboard("{Escape}");

  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
  expect(onSelect).not.toHaveBeenCalled();
});

test("Tab closes without choosing", async () => {
  const user = userEvent.setup();
  const { trigger, onSelect } = renderMenus();
  await user.click(trigger);

  await user.tab();

  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  expect(trigger).toHaveAttribute("aria-expanded", "false");
  expect(onSelect).not.toHaveBeenCalled();
});

test("a click outside closes without choosing", async () => {
  const user = userEvent.setup();
  const { trigger, onSelect } = renderMenus();
  await user.click(trigger);

  await user.click(document.body);

  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  expect(onSelect).not.toHaveBeenCalled();
});

test("moving the focus outside closes it", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenus();
  await user.click(trigger);

  await user.click(screen.getByRole("button", { name: "Fuera" }));

  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
});

test("the focus leaving without a click closes it", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenus();
  await user.click(trigger);

  act(() => screen.getByRole("button", { name: "Fuera" }).focus());

  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
});

test("opening a second menu closes the first", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenus();
  await user.click(trigger);

  await user.click(screen.getByRole("button", { name: "Dos: b" }));

  expect(screen.getAllByRole("menu")).toHaveLength(1);
  expect(screen.getByRole("menu", { name: "Dos" })).toBeInTheDocument();
  expect(trigger).toHaveAttribute("aria-expanded", "false");
});

test("a second click on the button closes the menu", async () => {
  const user = userEvent.setup();
  const { trigger } = renderMenus();
  await user.click(trigger);

  await user.click(trigger);

  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
});

test("an option can declare its language", async () => {
  const user = userEvent.setup();
  render(
    <MenuButton
      label="Idioma"
      menuLabel="Idioma"
      options={[{ value: "en", label: "English", lang: "en" }]}
      value="en"
      onSelect={vi.fn()}
    >
      EN
    </MenuButton>,
  );

  await user.click(screen.getByRole("button", { name: "Idioma" }));

  expect(screen.getByRole("menuitemradio", { name: "English" })).toHaveAttribute("lang", "en");
});
