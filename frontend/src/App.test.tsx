import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { App } from "./App";
import { createI18n } from "./i18n";
import { LANGUAGE_STORAGE_KEY, type LanguageStorage } from "./i18n/language";

test.each([
  ["es", "Confiabilidad", "Vista previa de los componentes"],
  ["pt-BR", "Confiabilidade", "Prévia dos componentes"],
  ["en", "Reliability", "Preview of the shared components"],
])("renders the application in %s", (language, heading, intro) => {
  render(
    <I18nextProvider i18n={createI18n(language)}>
      <App />
    </I18nextProvider>,
  );

  expect(screen.getByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
  expect(screen.getByText(intro, { exact: false })).toBeInTheDocument();
  expect(document.documentElement.lang).toBe(language);
});

test("switches the whole page language from the keyboard and remembers it", async () => {
  const user = userEvent.setup();
  const values = new Map<string, string>();
  const storage: LanguageStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  };
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <App storage={storage} />
    </I18nextProvider>,
  );

  await user.tab();
  await user.tab();
  await user.keyboard("{Enter}");

  const portuguese = screen.getByRole("button", { name: "Português (Brasil)" });
  expect(screen.getByRole("heading", { level: 1, name: "Confiabilidade" })).toBeInTheDocument();
  expect(document.documentElement.lang).toBe("pt-BR");
  expect(document.title).toBe("Confiabilidade — Componentes");
  expect(portuguese).toHaveFocus();
  expect(storage.getItem(LANGUAGE_STORAGE_KEY)).toBe("pt-BR");
});
