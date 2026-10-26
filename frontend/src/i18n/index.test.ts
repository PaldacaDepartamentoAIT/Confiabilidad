import { createI18n } from ".";
import { en } from "./locales/en";
import { es } from "./locales/es";

test("translates on first access without waiting", () => {
  const i18n = createI18n("pt-BR");

  expect(i18n.isInitialized).toBe(true);
  expect(i18n.language).toBe("pt-BR");
  expect(i18n.t("app.heading")).toBe("Confiabilidade");
});

test("falls back to English when a language lacks a text", () => {
  const i18n = createI18n("es", {
    es: { ...es, app: { title: es.app.title, intro: "" } },
    en,
  });

  expect(i18n.t("app.heading")).toBe("Reliability");
  expect(i18n.t("app.intro")).toBe(en.app.intro);
  expect(i18n.t("app.title")).toBe(es.app.title);
});
