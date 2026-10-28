import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { I18nextProvider } from "react-i18next";

import { App } from "./App";
import { createI18n } from "./i18n";
import { browserStorage, detectInitialLanguage } from "./i18n/language";
import { applyDocumentLanguage } from "./i18n/useDocumentLanguage";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element #root not found");
}

const storage = browserStorage();
const language = detectInitialLanguage(navigator.languages, storage);
// Antes de montar: Chrome fija el idioma de cada elemento al crearlo, y `index.html` dice `es`.
applyDocumentLanguage(language);
const i18n = createI18n(language);

createRoot(rootElement).render(
  <StrictMode>
    <I18nextProvider i18n={i18n}>
      <App storage={storage} />
    </I18nextProvider>
  </StrictMode>,
);
