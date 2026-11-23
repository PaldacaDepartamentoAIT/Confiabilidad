import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { createClient, environmentConfig, type ApiClient } from "./api/client";
import { HomePage } from "./auth/HomePage";
import { LoginPage } from "./auth/LoginPage";
import { TermsPage } from "./auth/TermsPage";
import { LiveAnnouncer } from "./components/LiveAnnouncer";
import type { LanguageStorage } from "./i18n/language";
import { useDocumentLanguage } from "./i18n/useDocumentLanguage";
import { DonePage } from "./registration/DonePage";
import { RegisterPage } from "./registration/RegisterPage";
import { VerifyPage } from "./registration/VerifyPage";
import { matchRoute, useLocation } from "./routing/router";
import { ShowcasePage } from "./showcase/ShowcasePage";

const ROUTES = [
  "/",
  "/login",
  "/terms",
  "/showcase",
  "/register",
  "/register/continue",
  "/register/done",
] as const;

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
      {route === "/" && <HomePage client={api} storage={storage} />}
      {route === "/login" && <LoginPage client={api} storage={storage} />}
      {route === "/terms" && <TermsPage client={api} storage={storage} />}
      {route === "/showcase" && <ShowcasePage storage={storage} />}
      {route === "/register" && <RegisterPage client={api} storage={storage} />}
      {route === "/register/continue" && <VerifyPage client={api} storage={storage} />}
      {route === "/register/done" && <DonePage storage={storage} />}
    </LiveAnnouncer>
  );
}
