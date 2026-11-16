import { useTranslation } from "react-i18next";

import { IconGlobe } from "../icons";
import {
  LANGUAGE_NAMES,
  SUPPORTED_LANGUAGES,
  persistLanguage,
  type Language,
  type LanguageStorage,
} from "../i18n/language";
import { Menu, type MenuOption } from "./menu/Menu";
import "../theme/ThemeButton.css";
import "./LanguageButton.css";

type LanguageButtonProps = {
  storage?: LanguageStorage;
  align?: "left" | "right";
};

const OPTIONS: MenuOption[] = SUPPORTED_LANGUAGES.map((language) => ({
  value: language,
  label: LANGUAGE_NAMES[language],
  lang: language,
}));

export function LanguageButton({ storage, align }: LanguageButtonProps) {
  const { t, i18n } = useTranslation();
  const current = i18n.language as Language;

  function choose(language: string) {
    void i18n.changeLanguage(language);
    if (storage) persistLanguage(language as Language, storage);
  }

  return (
    <Menu
      label={t("language.label")}
      options={OPTIONS}
      value={current}
      onSelect={choose}
      align={align}
      renderTrigger={(props) => (
        <button
          {...props}
          type="button"
          className="sb-btn hov"
          data-ui="sidebar-button"
          aria-label={`${t("language.label")}: ${LANGUAGE_NAMES[current]}`}
        >
          <IconGlobe />
          <span className="label mono">{current.split("-")[0].toUpperCase()}</span>
        </button>
      )}
    />
  );
}
