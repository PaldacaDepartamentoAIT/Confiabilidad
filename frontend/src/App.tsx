import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { getSession, type SessionInfo } from "./api/auth";
import { createClient, environmentConfig, type ApiClient, type TermsStatus } from "./api/client";
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

type AppProps = { storage?: LanguageStorage; client?: ApiClient };

const redirectFor = (route: string, info: SessionInfo | null): string | null => {
  if (!info) return route === "/terms" ? "/login" : null;
  if (route === "/login" || route === "/register") {
    return info.terms_status === "accepted" ? "/" : "/terms";
  }
  return route === "/terms" && info.terms_status === "accepted" ? "/" : null;
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
    }, 150);
    return () => window.clearTimeout(timer);
  }, [route, shownRoute]);

  useEffect(() => {
    if (route !== "/login" && route !== "/register" && route !== "/terms") return;
    if (session !== undefined) {
      const target = redirectFor(route, session);
      if (target) navigate(target);
      return;
    }
    let active = true;
    void getSession(api).then((result) => {
      if (!active) return;
      const next =
        result.kind === "ok" ? result.data : result.kind === "unauthenticated" ? null : undefined;
      if (next === undefined) return;
      setSession(next);
      const target = redirectFor(route, next);
      if (target) navigate(target);
    });
    return () => {
      active = false;
    };
  }, [api, route, session]);

  const setTerms = (terms_status: TermsStatus) =>
    setSession((cur) => (cur ? { ...cur, terms_status, terms: null } : cur));

  const screen =
    shownRoute === "/" ? (
      <HomePage
        client={api}
        session={session ?? undefined}
        storage={storage}
        onLoggedOut={() => setSession(null)}
        onTermsRequired={setTerms}
      />
    ) : shownRoute === "/login" ? (
      <LoginPage client={api} storage={storage} onAuthenticated={setSession} />
    ) : shownRoute === "/terms" ? (
      <TermsPage
        client={api}
        session={session ?? undefined}
        storage={storage}
        onAccepted={() => setTerms("accepted")}
        onLoggedOut={() => setSession(null)}
      />
    ) : shownRoute === "/showcase" ? (
      <ShowcasePage storage={storage} />
    ) : shownRoute === "/register" ? (
      <RegisterPage client={api} storage={storage} />
    ) : shownRoute === "/register/continue" ? (
      <VerifyPage client={api} storage={storage} />
    ) : (
      <DonePage storage={storage} />
    );

  return (
    <LiveAnnouncer>
      <TransitionPhaseContext.Provider value={phase}>
        {shownRoute === "/" ? screen : <PublicLayout storage={storage}>{screen}</PublicLayout>}
      </TransitionPhaseContext.Provider>
    </LiveAnnouncer>
  );
}
