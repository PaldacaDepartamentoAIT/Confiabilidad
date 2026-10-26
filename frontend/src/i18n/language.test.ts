import {
  LANGUAGE_NAMES,
  SUPPORTED_LANGUAGES,
  detectInitialLanguage,
  matchLanguage,
} from "./language";

test("supports Spanish, Brazilian Portuguese and English, each named in itself", () => {
  expect(SUPPORTED_LANGUAGES).toEqual(["es", "pt-BR", "en"]);
  expect(LANGUAGE_NAMES).toEqual({ es: "Español", "pt-BR": "Português (Brasil)", en: "English" });
});

test.each([
  ["es", "es"],
  ["es-MX", "es"],
  ["ES-es", "es"],
  ["pt", "pt-BR"],
  ["pt-BR", "pt-BR"],
  ["PT-pt", "pt-BR"],
  ["en", "en"],
  ["en-GB", "en"],
])("matches %s to %s", (tag, language) => {
  expect(matchLanguage(tag)).toBe(language);
});

test.each(["fr", "fr-FR", "de", "eo", "", "est", "english", "constructor", "toString-ES"])(
  "does not match %j",
  (tag) => {
    expect(matchLanguage(tag)).toBeNull();
  },
);

test("uses the first browser language that matches", () => {
  expect(detectInitialLanguage(["fr-FR", "pt-PT", "en"])).toBe("pt-BR");
  expect(detectInitialLanguage(["en-US", "es-ES"])).toBe("en");
});

test("falls back to English when no browser language matches", () => {
  expect(detectInitialLanguage(["fr-FR", "de"])).toBe("en");
  expect(detectInitialLanguage([])).toBe("en");
});
