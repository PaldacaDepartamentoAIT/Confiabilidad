import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { LANGUAGE_STORAGE_KEY, type LanguageStorage } from "../i18n/language";
import { LanguageSwitcher } from "./LanguageSwitcher";

function memoryStorage(): LanguageStorage {
  const values = new Map<string, string>();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  };
}

function renderSwitcher(language: string) {
  const i18n = createI18n(language);
  const storage = memoryStorage();
  render(
    <I18nextProvider i18n={i18n}>
      <LanguageSwitcher storage={storage} />
    </I18nextProvider>,
  );
  return { i18n, storage };
}

test("offers each language named in itself, marked with its own language", () => {
  renderSwitcher("es");

  const group = screen.getByRole("group", { name: "Idioma" });
  const buttons = within(group).getAllByRole("button");
  expect(buttons.map((button) => button.textContent)).toEqual([
    "Español",
    "Português (Brasil)",
    "English",
  ]);
  expect(buttons.map((button) => button.getAttribute("lang"))).toEqual(["es", "pt-BR", "en"]);
  expect(buttons.map((button) => button.getAttribute("aria-pressed"))).toEqual([
    "true",
    "false",
    "false",
  ]);
  buttons.forEach((button) => expect(button).toHaveAttribute("type", "button"));
});

test("changes, remembers and marks the language chosen with Enter, keeping the focus", async () => {
  const user = userEvent.setup();
  const { i18n, storage } = renderSwitcher("es");

  await user.tab();
  await user.tab();
  await user.tab();
  const english = screen.getByRole("button", { name: "English" });
  expect(english).toHaveFocus();

  await user.keyboard("{Enter}");

  expect(i18n.language).toBe("en");
  expect(storage.getItem(LANGUAGE_STORAGE_KEY)).toBe("en");
  expect(screen.getByRole("group", { name: "Language" })).toBeInTheDocument();
  expect(english).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("button", { name: "Español" })).toHaveAttribute("aria-pressed", "false");
  expect(english).toHaveFocus();
});

test("changes the language with Space", async () => {
  const user = userEvent.setup();
  const { i18n, storage } = renderSwitcher("en");

  await user.tab();
  await user.tab();
  expect(screen.getByRole("button", { name: "Português (Brasil)" })).toHaveFocus();

  await user.keyboard(" ");

  expect(i18n.language).toBe("pt-BR");
  expect(storage.getItem(LANGUAGE_STORAGE_KEY)).toBe("pt-BR");
  expect(screen.getByRole("button", { name: "Português (Brasil)" })).toHaveFocus();
});
