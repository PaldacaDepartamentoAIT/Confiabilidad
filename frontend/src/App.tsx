import { useTranslation } from "react-i18next";

import { LanguageSwitcher } from "./components/LanguageSwitcher";
import type { LanguageStorage } from "./i18n/language";
import { useDocumentLanguage } from "./i18n/useDocumentLanguage";

type AppProps = {
  storage?: LanguageStorage;
};

export function App({ storage }: AppProps) {
  const { t } = useTranslation();
  useDocumentLanguage();

  return (
    <main>
      <LanguageSwitcher storage={storage} />
      <h1>{t("app.heading")}</h1>
      <p>{t("app.intro")}</p>
    </main>
  );
}
