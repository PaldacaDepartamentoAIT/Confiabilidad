import { useTranslation } from "react-i18next";

import {
  LANGUAGE_NAMES,
  SUPPORTED_LANGUAGES,
  persistLanguage,
  type Language,
  type LanguageStorage,
} from "../i18n/language";

type LanguageSwitcherProps = {
  storage?: LanguageStorage;
};

export function LanguageSwitcher({ storage }: LanguageSwitcherProps) {
  const { t, i18n } = useTranslation();

  function choose(language: Language) {
    void i18n.changeLanguage(language);
    if (storage) persistLanguage(language, storage);
  }

  return (
    <div role="group" aria-label={t("language.label")}>
      {SUPPORTED_LANGUAGES.map((language) => (
        <button
          key={language}
          type="button"
          lang={language}
          aria-pressed={i18n.language === language}
          onClick={() => choose(language)}
        >
          {LANGUAGE_NAMES[language]}
        </button>
      ))}
    </div>
  );
}
