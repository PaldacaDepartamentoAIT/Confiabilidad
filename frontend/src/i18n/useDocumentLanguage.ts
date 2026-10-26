import { useEffect } from "react";
import { useTranslation } from "react-i18next";

export function useDocumentLanguage(): void {
  const { t, i18n } = useTranslation();
  const language = i18n.language;
  const title = t("app.title");

  useEffect(() => {
    document.documentElement.lang = language;
    document.title = title;
  }, [language, title]);
}
