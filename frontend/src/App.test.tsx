import { render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";

import { App } from "./App";
import { createI18n } from "./i18n";

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
