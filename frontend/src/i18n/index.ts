import i18next, { type i18n, type Resource } from "i18next";
import { initReactI18next } from "react-i18next";

import { en } from "./locales/en";
import { es } from "./locales/es";
import { ptBR } from "./locales/pt-BR";

export const defaultNamespace = "translation";

const messages = { es, "pt-BR": ptBR, en };

function toResource(locales: Record<string, unknown>): Resource {
  return Object.fromEntries(
    Object.entries(locales).map(([language, texts]) => [language, { [defaultNamespace]: texts }]),
  ) as Resource;
}

export function createI18n(language: string, locales: Record<string, unknown> = messages): i18n {
  const instance = i18next.createInstance();
  void instance.use(initReactI18next).init({
    lng: language,
    fallbackLng: "en",
    defaultNS: defaultNamespace,
    resources: toResource(locales),
    initAsync: false,
    returnNull: false,
    returnEmptyString: false,
    interpolation: { escapeValue: false },
  });
  return instance;
}
