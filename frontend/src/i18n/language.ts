export const SUPPORTED_LANGUAGES = ["es", "pt-BR", "en"] as const;

export type Language = (typeof SUPPORTED_LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = "en";

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

export function detectInitialLanguage(navigatorLanguages: readonly string[]): Language {
  for (const tag of navigatorLanguages) {
    const language = matchLanguage(tag);
    if (language) return language;
  }
  return DEFAULT_LANGUAGE;
}
