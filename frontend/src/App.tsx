import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { getSession, type SessionInfo } from "./api/auth";
import { createClient, environmentConfig, type ApiClient, type TermsStatus } from "./api/client";
import { HomePage } from "./auth/HomePage";
import { LoginPage } from "./auth/LoginPage";
import { ProfilePage } from "./auth/ProfilePage";
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
  "/profile",
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
      return setPhase("idle");
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
    const go = (info: SessionInfo | null) => {
      const target = redirectFor(route, info);
      if (target) navigate(target);
    };
    if (session !== undefined) return go(session);
    let active = true;
    void getSession(api).then((r) => {
      const next = r.kind === "ok" ? r.data : r.kind === "unauthenticated" ? null : undefined;
      if (!active || next === undefined) return;
      setSession(next);
      go(next);
    });
    return () => {
      active = false;
    };
  }, [api, route, session]);

  const setTerms = (terms_status: TermsStatus) =>
    setSession((cur) => (cur ? { ...cur, terms_status, terms: null } : cur));
  const shared = { client: api, storage };
  const withSession = {
    ...shared,
    session: session ?? undefined,
    onLoggedOut: () => setSession(null),
  };

  const screen = {
    "/": <HomePage {...withSession} onTermsRequired={setTerms} />,
    "/profile": <ProfilePage {...withSession} onTermsRequired={setTerms} />,
    "/login": <LoginPage {...shared} onAuthenticated={setSession} />,
    "/terms": <TermsPage {...withSession} onAccepted={() => setTerms("accepted")} />,
    "/showcase": <ShowcasePage storage={storage} />,
    "/register": <RegisterPage {...shared} />,
    "/register/continue": <VerifyPage {...shared} />,
    "/register/done": <DonePage storage={storage} />,
  }[shownRoute];

  return (
    <LiveAnnouncer>
      <TransitionPhaseContext.Provider value={phase}>
        {shownRoute === "/" || shownRoute === "/profile" ? (
          screen
        ) : (
          <PublicLayout storage={storage}>{screen}</PublicLayout>
        )}
      </TransitionPhaseContext.Provider>
    </LiveAnnouncer>
  );
}
