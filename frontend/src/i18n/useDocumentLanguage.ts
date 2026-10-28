import { useEffect } from "react";
import { useTranslation } from "react-i18next";

export function applyDocumentLanguage(language: string): void {
  document.documentElement.lang = language;
}

export function useDocumentLanguage(): void {
  const { t, i18n } = useTranslation();
  const language = i18n.language;
  const title = t("app.title");

  useEffect(() => {
    applyDocumentLanguage(language);
    document.title = title;
  }, [language, title]);
}
