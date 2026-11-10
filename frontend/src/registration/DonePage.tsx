import { useTranslation } from "react-i18next";

import type { LanguageStorage } from "../i18n/language";
import { PublicLayout } from "../layouts/PublicLayout";

// La cuenta queda creada sin iniciar sesión: el inicio de sesión no es de esta feature (S-07).
export function DonePage({ storage }: { storage?: LanguageStorage }) {
  const { t } = useTranslation();
  return (
    <PublicLayout storage={storage}>
      <main>
        <h1>{t("register.doneTitle")}</h1>
        <p>{t("register.doneText")}</p>
      </main>
    </PublicLayout>
  );
}
