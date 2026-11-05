import { useTranslation } from "react-i18next";

import {
  LANGUAGE_NAMES,
  SUPPORTED_LANGUAGES,
  persistLanguage,
  type Language,
  type LanguageStorage,
} from "../i18n/language";
import { MenuButton } from "./MenuButton";

const SHORT_NAMES: Record<Language, string> = { es: "ES", "pt-BR": "PT", en: "EN" };

const OPTIONS = SUPPORTED_LANGUAGES.map((language) => ({
  value: language,
  label: LANGUAGE_NAMES[language],
  lang: language,
}));

type LanguageMenuProps = {
  storage?: LanguageStorage;
};

export function LanguageMenu({ storage }: LanguageMenuProps) {
  const { t, i18n } = useTranslation();
  const active = i18n.language as Language;

  function choose(language: Language) {
    void i18n.changeLanguage(language);
    if (storage) persistLanguage(language, storage);
  }

  // El nombre accesible incluye la abreviatura visible (WCAG 2.5.3).
  const name = `${LANGUAGE_NAMES[active]} (${SHORT_NAMES[active]})`;

  return (
    <MenuButton
      label={t("topBar.language", { name })}
      menuLabel={t("language.label")}
      options={OPTIONS}
      value={active}
      onSelect={choose}
    >
      {SHORT_NAMES[active]}
    </MenuButton>
  );
}
