import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { LANGUAGE_STORAGE_KEY, type LanguageStorage } from "../i18n/language";
import { LanguageButton } from "./LanguageButton";

function memoryStorage(): LanguageStorage & { values: Map<string, string> } {
  const values = new Map<string, string>();
  return {
    values,
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  };
}

function renderButton(language = "es", storage?: LanguageStorage) {
  const i18n = createI18n(language);
  const view = render(
    <I18nextProvider i18n={i18n}>
      <LanguageButton storage={storage} />
    </I18nextProvider>,
  );
  return { ...view, i18n };
}

test("shows the code of the active language and names it for screen readers", () => {
  renderButton("es");

  const button = screen.getByRole("combobox", { name: "Idioma: Español" });
  expect(button).toHaveTextContent("ES");
  expect(button).toHaveAttribute("data-ui", "sidebar-button");
  expect(button).toHaveClass("sb-btn", "hov");
  expect(button.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
});

test.each([
  ["pt-BR", "PT", "Idioma: Português (Brasil)", "Idioma"],
  ["en", "EN", "Language: English", "Language"],
])("%s shows %s", (language, code, name) => {
  renderButton(language);
  expect(screen.getByRole("combobox", { name })).toHaveTextContent(new RegExp(`^${code}$`));
});

test("opens a list with the three languages, each named in itself, the active one selected", async () => {
  const user = userEvent.setup();
  renderButton("pt-BR");

  await user.click(screen.getByRole("combobox"));

  const listbox = screen.getByRole("listbox", { name: "Idioma" });
  const options = screen.getAllByRole("option");
  expect(options.map((option) => option.textContent)).toEqual([
    "Español",
    "Português (Brasil)",
    "English",
  ]);
  expect(options.map((option) => option.getAttribute("lang"))).toEqual(["es", "pt-BR", "en"]);
  expect(options[1]).toHaveAttribute("aria-selected", "true");
  expect(listbox).toBeInTheDocument();
});

test("choosing a language changes the interface, the code and the name, and saves it", async () => {
  const user = userEvent.setup();
  const storage = memoryStorage();
  const { i18n } = renderButton("es", storage);

  await user.click(screen.getByRole("combobox"));
  await user.click(screen.getByRole("option", { name: "English" }));

  expect(i18n.language).toBe("en");
  expect(storage.values.get(LANGUAGE_STORAGE_KEY)).toBe("en");
  const button = await screen.findByRole("combobox", { name: "Language: English" });
  expect(button).toHaveTextContent("EN");
  expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
});

test("works from the keyboard", async () => {
  const user = userEvent.setup();
  const { i18n } = renderButton("es");

  await user.tab();
  expect(screen.getByRole("combobox")).toHaveFocus();
  await user.keyboard("{ArrowDown}{ArrowDown}{Enter}");

  expect(i18n.language).toBe("pt-BR");
  expect(screen.getByRole("combobox")).toHaveFocus();
});

test("changes the language even when there is no storage to save it in", async () => {
  const user = userEvent.setup();
  const { i18n } = renderButton("es");

  await user.click(screen.getByRole("combobox"));
  await user.click(screen.getByRole("option", { name: "English" }));

  expect(i18n.language).toBe("en");
});

test("has no accessibility violations closed and open", async () => {
  const user = userEvent.setup();
  const { container } = renderButton("es");
  const run = () => axe.run(container, { rules: { "color-contrast": { enabled: false } } });

  expect((await run()).violations).toEqual([]);
  await user.click(screen.getByRole("combobox"));
  expect((await run()).violations).toEqual([]);
});
