export const SUPPORTED_LANGUAGES = ["es", "pt-BR", "en"] as const;

export type Language = (typeof SUPPORTED_LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = "en";

export const LANGUAGE_STORAGE_KEY = "confiabilidad.language";

export type LanguageStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

export const LANGUAGE_NAMES: Record<Language, string> = {
  es: "Español",
  "pt-BR": "Português (Brasil)",
  en: "English",
};

const PRIMARY_SUBTAGS = new Map<string, Language>([
  ["es", "es"],
  ["pt", "pt-BR"],
  ["en", "en"],
]);

export function matchLanguage(tag: string): Language | null {
  const primary = tag.split("-")[0].toLowerCase();
  return PRIMARY_SUBTAGS.get(primary) ?? null;
}

function isSupported(value: string): value is Language {
  return (SUPPORTED_LANGUAGES as readonly string[]).includes(value);
}

// Si el navegador bloquea el almacenamiento, se actúa como si no hubiera nada guardado (S-04).
function attempt<T>(action: () => T): T | undefined {
  try {
    return action();
  } catch {
    return undefined;
  }
}

export function browserStorage(): LanguageStorage | undefined {
  return attempt(() => window.localStorage);
}

function readStoredLanguage(storage: LanguageStorage): Language | null {
  const stored = attempt(() => storage.getItem(LANGUAGE_STORAGE_KEY)) ?? null;
  if (stored === null) return null;
  if (isSupported(stored)) return stored;
  attempt(() => storage.removeItem(LANGUAGE_STORAGE_KEY));
  return null;
}

export function persistLanguage(language: Language, storage: LanguageStorage): void {
  attempt(() => storage.setItem(LANGUAGE_STORAGE_KEY, language));
}

export function detectInitialLanguage(
  navigatorLanguages: readonly string[],
  storage?: LanguageStorage,
): Language {
  const stored = storage ? readStoredLanguage(storage) : null;
  if (stored) return stored;
  for (const tag of navigatorLanguages) {
    const language = matchLanguage(tag);
    if (language) return language;
  }
  return DEFAULT_LANGUAGE;
}
