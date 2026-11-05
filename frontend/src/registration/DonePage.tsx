import { useTranslation } from "react-i18next";

import { LanguageSwitcher } from "../components/LanguageSwitcher";
import type { LanguageStorage } from "../i18n/language";

// La cuenta queda creada sin iniciar sesión: el inicio de sesión no es de esta feature (S-07).
export function DonePage({ storage }: { storage?: LanguageStorage }) {
  const { t } = useTranslation();
  return (
    <main>
      <LanguageSwitcher storage={storage} />
      <h1>{t("register.doneTitle")}</h1>
      <p>{t("register.doneText")}</p>
    </main>
  );
}
