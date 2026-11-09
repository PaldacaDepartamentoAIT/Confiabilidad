import "@fontsource-variable/manrope";
import "@fontsource-variable/jetbrains-mono";
import "./styles/tokens.css";
import "./styles/base.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { I18nextProvider } from "react-i18next";

import { App } from "./App";
import { createI18n } from "./i18n";
import { browserStorage, detectInitialLanguage } from "./i18n/language";
import { initTheme } from "./theme/theme";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element #root not found");
}

const storage = browserStorage();
// El tema se aplica antes de renderizar para que no parpadee el tema equivocado.
initTheme({ storage });
const i18n = createI18n(detectInitialLanguage(navigator.languages, storage));

createRoot(rootElement).render(
  <StrictMode>
    <I18nextProvider i18n={i18n}>
      <App storage={storage} />
    </I18nextProvider>
  </StrictMode>,
);
