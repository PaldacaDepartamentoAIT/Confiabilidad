import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { createClient, environmentConfig, type ApiClient } from "./api/client";
import { LiveAnnouncer } from "./components/LiveAnnouncer";
import type { LanguageStorage } from "./i18n/language";
import { useDocumentLanguage } from "./i18n/useDocumentLanguage";
import { DonePage } from "./registration/DonePage";
import { RegisterPage } from "./registration/RegisterPage";
import { VerifyPage } from "./registration/VerifyPage";
import { PublicLayout } from "./layouts/PublicLayout";
import { matchRoute, useLocation } from "./routing/router";
import { ShowcasePage } from "./showcase/ShowcasePage";

// La página de muestra sigue siendo la de inicio y la de reserva (S-06 de componentes-base-accesibles).
const ROUTES = ["/", "/register", "/register/continue", "/register/done"] as const;

type AppProps = {
  storage?: LanguageStorage;
  client?: ApiClient;
};

export function App({ storage, client }: AppProps) {
  useDocumentLanguage();
  const { i18n } = useTranslation();
  const api = useMemo(
    () => client ?? createClient(environmentConfig(() => i18n.language)),
    [client, i18n],
  );
  const route = matchRoute(useLocation().path, ROUTES, "/");
  return (
    <LiveAnnouncer>
      {route === "/" ? (
        <ShowcasePage storage={storage} />
      ) : (
        // Una sola barra para todo el registro: al cambiar de pantalla es el mismo nodo, no se repinta (RF-009).
        <PublicLayout storage={storage}>
          {route === "/register" && <RegisterPage client={api} />}
          {route === "/register/continue" && <VerifyPage client={api} />}
          {route === "/register/done" && <DonePage />}
        </PublicLayout>
      )}
    </LiveAnnouncer>
  );
}
