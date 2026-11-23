import { useTranslation } from "react-i18next";

import type { LanguageStorage } from "../i18n/language";
import { PublicLayout } from "../layouts/PublicLayout";
import { PublicPage } from "../layouts/PublicPage";
import { navigate } from "../routing/router";

// La cuenta queda creada sin iniciar sesión: al pulsar el enlace lleva a `/login` sin recargar.
export function DonePage({ storage }: { storage?: LanguageStorage }) {
  const { t } = useTranslation();
  return (
    <PublicLayout storage={storage}>
      <PublicPage title={t("register.doneTitle")}>
        <p>{t("register.doneText")}</p>
        <div className="public-actions-row">
          <a
            href="/login"
            className="btn btn-primary"
            onClick={(event) => {
              event.preventDefault();
              navigate("/login");
            }}
          >
            {t("register.signInLink")}
          </a>
        </div>
      </PublicPage>
    </PublicLayout>
  );
}
