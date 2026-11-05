import { useTranslation } from "react-i18next";

import type { LanguageStorage } from "../i18n/language";
import { LanguageMenu } from "./LanguageMenu";

type TopBarProps = {
  storage?: LanguageStorage;
};

export function TopBar({ storage }: TopBarProps) {
  const { t } = useTranslation();
  return (
    <header className="top-bar" aria-label={t("topBar.label")}>
      <LanguageMenu storage={storage} />
    </header>
  );
}
