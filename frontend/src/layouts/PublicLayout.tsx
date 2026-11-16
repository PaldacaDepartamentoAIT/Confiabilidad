import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { LanguageButton } from "../components/LanguageButton";
import type { LanguageStorage } from "../i18n/language";
import { ThemeButton } from "../theme/ThemeButton";
import "./PublicLayout.css";

type PublicLayoutProps = {
  storage?: LanguageStorage;
  children: ReactNode;
};

// Diseño de las pantallas sin sesión: solo una barra superior con el nombre del sistema y los
// botones de idioma y de tema; el contenido va debajo, con su propio `<main>`.
export function PublicLayout({ storage, children }: PublicLayoutProps) {
  const { t } = useTranslation();
  return (
    <div className="public-app">
      <header className="public-bar" data-ui="topbar">
        <p className="brand" data-ui="brand">
          {t("app.heading")}
        </p>
        <div className="public-actions">
          <LanguageButton storage={storage} align="right" />
          <ThemeButton storage={storage} />
        </div>
      </header>
      <div className="public-content">{children}</div>
    </div>
  );
}
