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
import { PublicLayout } from "./layouts/PublicLayout";
import { TransitionPhaseContext, type TransitionPhase } from "./layouts/screenTransition";
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

const FADE_OUT_MS = 150;

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
  const [shownRoute, setShownRoute] = useState(route);
  const [phase, setPhase] = useState<TransitionPhase>("idle");
  const [session, setSession] = useState<SessionInfo | null | undefined>(undefined);

  useEffect(() => {
    if (route === shownRoute) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
      setShownRoute(route);
      setPhase("idle");
      return;
    }
    setPhase("out");
    const timer = window.setTimeout(() => {
      setShownRoute(route);
      setPhase("in");
    }, FADE_OUT_MS);
    return () => window.clearTimeout(timer);
  }, [route, shownRoute]);

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

  const screen = (
    <>
      {shownRoute === "/" && (
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
      {shownRoute === "/login" && (
        <LoginPage
          client={api}
          storage={storage}
          onAuthenticated={(authenticated) => setSession(authenticated)}
        />
      )}
      {shownRoute === "/terms" && (
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
      {shownRoute === "/showcase" && <ShowcasePage storage={storage} />}
      {shownRoute === "/register" && <RegisterPage client={api} storage={storage} />}
      {shownRoute === "/register/continue" && <VerifyPage client={api} storage={storage} />}
      {shownRoute === "/register/done" && <DonePage storage={storage} />}
    </>
  );

  return (
    <LiveAnnouncer>
      <TransitionPhaseContext.Provider value={phase}>
        {shownRoute === "/" ? screen : <PublicLayout storage={storage}>{screen}</PublicLayout>}
      </TransitionPhaseContext.Provider>
    </LiveAnnouncer>
  );
}
