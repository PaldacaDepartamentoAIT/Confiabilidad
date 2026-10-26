import {
  LANGUAGE_NAMES,
  LANGUAGE_STORAGE_KEY,
  SUPPORTED_LANGUAGES,
  browserStorage,
  detectInitialLanguage,
  matchLanguage,
  persistLanguage,
  type LanguageStorage,
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

function memoryStorage(initial: Record<string, string> = {}): LanguageStorage {
  const values = new Map(Object.entries(initial));
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  };
}

const brokenStorage: LanguageStorage = {
  getItem: () => {
    throw new Error("blocked");
  },
  setItem: () => {
    throw new Error("blocked");
  },
  removeItem: () => {
    throw new Error("blocked");
  },
};

test("persists the chosen language", () => {
  const storage = memoryStorage();

  persistLanguage("pt-BR", storage);

  expect(storage.getItem(LANGUAGE_STORAGE_KEY)).toBe("pt-BR");
  expect(LANGUAGE_STORAGE_KEY).toBe("confiabilidad.language");
});

test("prefers a valid stored language over the browser languages", () => {
  const storage = memoryStorage({ [LANGUAGE_STORAGE_KEY]: "es" });

  expect(detectInitialLanguage(["pt-BR"], storage)).toBe("es");
});

test("removes an invalid stored language and uses the browser languages", () => {
  const storage = memoryStorage({ [LANGUAGE_STORAGE_KEY]: "fr" });

  expect(detectInitialLanguage(["pt-BR"], storage)).toBe("pt-BR");
  expect(storage.getItem(LANGUAGE_STORAGE_KEY)).toBeNull();
});

test("ignores a stored value that only looks like a language", () => {
  const storage = memoryStorage({ [LANGUAGE_STORAGE_KEY]: "pt" });

  expect(detectInitialLanguage(["fr"], storage)).toBe("en");
  expect(storage.getItem(LANGUAGE_STORAGE_KEY)).toBeNull();
});

test("behaves as if nothing were stored when the storage throws", () => {
  expect(detectInitialLanguage(["es-MX"], brokenStorage)).toBe("es");
  expect(() => persistLanguage("en", brokenStorage)).not.toThrow();
});

test("returns no storage when the browser blocks access to it", () => {
  const descriptor = Object.getOwnPropertyDescriptor(window, "localStorage");
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    get: () => {
      throw new DOMException("denied", "SecurityError");
    },
  });
  try {
    expect(browserStorage()).toBeUndefined();
  } finally {
    if (descriptor) Object.defineProperty(window, "localStorage", descriptor);
  }
  expect(browserStorage()).toBe(window.localStorage);
});
