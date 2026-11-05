import { useTranslation } from "react-i18next";

// La cuenta queda creada sin iniciar sesión: el inicio de sesión no es de esta feature (S-07).
export function DonePage() {
  const { t } = useTranslation();
  return (
    <main>
      <h1>{t("register.doneTitle")}</h1>
      <p>{t("register.doneText")}</p>
    </main>
  );
}
