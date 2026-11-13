import { useTranslation } from "react-i18next";

import { PublicPage } from "../layouts/PublicPage";

// La cuenta queda creada sin iniciar sesión: el inicio de sesión no es de esta feature (S-07).
export function DonePage() {
  const { t } = useTranslation();
  return (
    <PublicPage title={t("register.doneTitle")}>
      <p>{t("register.doneText")}</p>
    </PublicPage>
  );
}
