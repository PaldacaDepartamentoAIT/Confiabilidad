import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { getSession, type SessionInfo } from "./api/auth";
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
import { matchRoute, navigate, useLocation } from "./routing/router";
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
  const [session, setSession] = useState<SessionInfo | null | undefined>(undefined);

  useEffect(() => {
    const needsSessionCheck = route === "/login" || route === "/register" || route === "/terms";
    if (!needsSessionCheck) return;

    if (session) {
      if (route === "/login" || route === "/register") {
        navigate(session.terms_status === "accepted" ? "/" : "/terms");
      } else if (route === "/terms" && session.terms_status === "accepted") {
        navigate("/");
      }
      return;
    }

    if (session === null) {
      if (route === "/terms") navigate("/login");
      return;
    }

    let active = true;
    void getSession(api).then((result) => {
      if (!active) return;
      if (result.kind === "ok") {
        setSession(result.data);
        if (route === "/login" || route === "/register") {
          navigate(result.data.terms_status === "accepted" ? "/" : "/terms");
        } else if (route === "/terms" && result.data.terms_status === "accepted") {
          navigate("/");
        }
      } else if (result.kind === "unauthenticated") {
        setSession(null);
        if (route === "/terms") navigate("/login");
      }
    });
    return () => {
      active = false;
    };
  }, [api, route, session]);

  return (
    <LiveAnnouncer>
      {route === "/" && (
        <HomePage
          client={api}
          session={session ?? undefined}
          storage={storage}
          onLoggedOut={() => setSession(null)}
          onTermsRequired={(termsStatus) =>
            setSession((current) => (current ? { ...current, terms_status: termsStatus } : current))
          }
        />
      )}
      {route === "/login" && (
        <LoginPage
          client={api}
          storage={storage}
          onAuthenticated={(authenticated) => setSession(authenticated)}
        />
      )}
      {route === "/terms" && (
        <TermsPage
          client={api}
          session={session ?? undefined}
          storage={storage}
          onAccepted={() =>
            setSession((current) =>
              current ? { ...current, terms_status: "accepted", terms: null } : current,
            )
          }
          onLoggedOut={() => setSession(null)}
        />
      )}
      {route === "/showcase" && <ShowcasePage storage={storage} />}
      {route === "/register" && <RegisterPage client={api} storage={storage} />}
      {route === "/register/continue" && <VerifyPage client={api} storage={storage} />}
      {route === "/register/done" && <DonePage storage={storage} />}
    </LiveAnnouncer>
  );
}
