import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { I18nextProvider } from "react-i18next";

import { App } from "./App";
import { createI18n } from "./i18n";
import { browserStorage, detectInitialLanguage } from "./i18n/language";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element #root not found");
}

const storage = browserStorage();
const i18n = createI18n(detectInitialLanguage(navigator.languages, storage));

createRoot(rootElement).render(
  <StrictMode>
    <I18nextProvider i18n={i18n}>
      <App storage={storage} />
    </I18nextProvider>
  </StrictMode>,
);
