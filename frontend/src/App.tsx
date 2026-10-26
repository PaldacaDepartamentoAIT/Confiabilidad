import { useTranslation } from "react-i18next";

import { useDocumentLanguage } from "./i18n/useDocumentLanguage";

export function App() {
  const { t } = useTranslation();
  useDocumentLanguage();

  return (
    <main>
      <h1>{t("app.heading")}</h1>
      <p>{t("app.intro")}</p>
    </main>
  );
}
