import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { LANGUAGE_STORAGE_KEY, type LanguageStorage } from "../i18n/language";
import { LanguageMenu } from "./LanguageMenu";

function memoryStorage(): LanguageStorage {
  const values = new Map<string, string>();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  };
}

function renderMenu(language: string) {
  const i18n = createI18n(language);
  const storage = memoryStorage();
  render(
    <I18nextProvider i18n={i18n}>
      <LanguageMenu storage={storage} />
      <label>
        Nota
        <input />
      </label>
    </I18nextProvider>,
  );
  return { i18n, storage };
}

test.each([
  ["es", "ES", "Idioma: Español (ES)"],
  ["en", "EN", "Language: English (EN)"],
  ["pt-BR", "PT", "Idioma: Português (Brasil) (PT)"],
])("in %s the button shows %s and names the active language", (language, short, name) => {
  renderMenu(language);

  const button = screen.getByRole("button", { name });
  expect(button).toHaveTextContent(short);
  expect(button).toHaveAttribute("aria-haspopup", "menu");
});

test("offers each language named in itself, marked with its own language", async () => {
  const user = userEvent.setup();
  renderMenu("es");

  await user.click(screen.getByRole("button", { name: "Idioma: Español (ES)" }));

  const items = screen.getAllByRole("menuitemradio");
  expect(screen.getByRole("menu", { name: "Idioma" })).toBeInTheDocument();
  expect(items.map((item) => item.textContent)).toEqual([
    "Español",
    "Português (Brasil)",
    "English",
  ]);
  expect(items.map((item) => item.getAttribute("lang"))).toEqual(["es", "pt-BR", "en"]);
  expect(items.map((item) => item.getAttribute("aria-checked"))).toEqual([
    "true",
    "false",
    "false",
  ]);
});

test("moving with the arrows does not change the language", async () => {
  const user = userEvent.setup();
  const { i18n } = renderMenu("es");
  await user.click(screen.getByRole("button", { name: "Idioma: Español (ES)" }));

  await user.keyboard("{ArrowDown}{ArrowDown}");

  expect(i18n.language).toBe("es");
  expect(screen.getByRole("menuitemradio", { name: "English" })).toHaveFocus();
});

test("changes and remembers the chosen language, keeping the focus and what was typed", async () => {
  const user = userEvent.setup();
  const { i18n, storage } = renderMenu("es");
  await user.type(screen.getByRole("textbox", { name: "Nota" }), "hola");
  await user.click(screen.getByRole("button", { name: "Idioma: Español (ES)" }));

  await user.keyboard("{ArrowDown}{ArrowDown}{Enter}");

  expect(i18n.language).toBe("en");
  expect(storage.getItem(LANGUAGE_STORAGE_KEY)).toBe("en");
  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  const button = screen.getByRole("button", { name: "Language: English (EN)" });
  expect(button).toHaveFocus();
  expect(screen.getByRole("textbox", { name: "Nota" })).toHaveValue("hola");

  await user.click(button);
  expect(screen.getByRole("menuitemradio", { name: "English" })).toHaveAttribute(
    "aria-checked",
    "true",
  );
});

test("changes the language with a click", async () => {
  const user = userEvent.setup();
  const { i18n, storage } = renderMenu("en");
  await user.click(screen.getByRole("button", { name: "Language: English (EN)" }));

  await user.click(screen.getByRole("menuitemradio", { name: "Português (Brasil)" }));

  expect(i18n.language).toBe("pt-BR");
  expect(storage.getItem(LANGUAGE_STORAGE_KEY)).toBe("pt-BR");
});

test("works without storage", async () => {
  const user = userEvent.setup();
  const i18n = createI18n("en");
  render(
    <I18nextProvider i18n={i18n}>
      <LanguageMenu />
    </I18nextProvider>,
  );
  await user.click(screen.getByRole("button", { name: "Language: English (EN)" }));

  await user.click(screen.getByRole("menuitemradio", { name: "Español" }));

  expect(i18n.language).toBe("es");
});
