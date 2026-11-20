import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  getSession,
  listSessions,
  logout,
  revokeOtherSessions,
  revokeSession,
  type ActiveSessionItem,
  type AuthenticatedUser,
  type SessionInfo,
} from "../api/auth";
import type { ApiClient, TermsStatus } from "../api/client";
import { Block } from "../components/Block";
import { Button } from "../components/Button";
import { Chip } from "../components/Chip";
import { FormMessage } from "../components/FormMessage";
import { IconButton } from "../components/IconButton";
import { Table, type TableColumn, type TableRow } from "../components/data/Table";
import type { LanguageStorage } from "../i18n/language";
import { IconHouse, IconLogOut } from "../icons";
import { AppLayout } from "../layouts/AppLayout";
import type { SidebarItem } from "../layouts/Sidebar";
import { translateCode } from "../registration/serverErrors";
import { navigate } from "../routing/router";
import type { TokenStorage } from "./tokenStorage";

type HomePageProps = {
  client: ApiClient;
  session?: SessionInfo | null;
  storage?: LanguageStorage;
  tokenStorage?: TokenStorage;
  onLoggedOut?: () => void;
  onTermsRequired?: (termsStatus: TermsStatus) => void;
};

function userInitials(user: AuthenticatedUser | null): string {
  const source = (user?.name || user?.email || "U").trim();
  const parts = source.split(/\s+/);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return source.slice(0, 2).toUpperCase();
}

function formatTimestamp(iso: string, language: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return new Intl.DateTimeFormat(language, {
    dateStyle: "short",
    timeStyle: "short",
  }).format(parsed);
}

export function HomePage({
  client,
  session,
  storage,
  tokenStorage,
  onLoggedOut,
  onTermsRequired,
}: HomePageProps) {
  const { t, i18n } = useTranslation();
  const [user, setUser] = useState<AuthenticatedUser | null>(session?.user ?? null);
  const [sessions, setSessions] = useState<ActiveSessionItem[]>([]);
  const [errorKey, setErrorKey] = useState<string | null>(null);
  const loggingOut = useRef(false);
  const [revokingId, setRevokingId] = useState<number | null>(null);
  const [revokingOthers, setRevokingOthers] = useState(false);

  const redirectToLogin = useCallback(() => {
    tokenStorage?.clear();
    onLoggedOut?.();
    navigate("/login");
  }, [onLoggedOut, tokenStorage]);

  const redirectToTerms = useCallback(
    (termsStatus: TermsStatus) => {
      onTermsRequired?.(termsStatus);
      navigate("/terms");
    },
    [onTermsRequired],
  );

  const handleOutcomeFailure = useCallback(
    (result: { kind: string; termsStatus?: TermsStatus; code?: string }) => {
      if (result.kind === "unauthenticated") {
        redirectToLogin();
        return;
      }
      if (result.kind === "termsRequired") {
        redirectToTerms(result.termsStatus ?? "not_accepted");
        return;
      }
      if (result.kind === "refused" && result.code) {
        setErrorKey(`validation.${translateCode(result.code).key}`);
      } else if (result.kind === "networkError") {
        setErrorKey("validation.networkError");
      } else {
        setErrorKey("validation.serverError");
      }
    },
    [redirectToLogin, redirectToTerms],
  );

  useEffect(() => {
    let active = true;
    async function load() {
      if (!session) {
        const info = await getSession(client);
        if (!active) return;
        if (info.kind !== "ok") {
          handleOutcomeFailure(info);
          return;
        }
        setUser(info.data.user);
        if (info.data.terms_status !== "accepted") {
          redirectToTerms(info.data.terms_status);
          return;
        }
      } else {
        setUser(session.user);
        if (session.terms_status !== "accepted") {
          redirectToTerms(session.terms_status);
          return;
        }
      }
      const listed = await listSessions(client);
      if (!active) return;
      if (listed.kind === "ok") {
        setErrorKey(null);
        setSessions(listed.data.sessions);
      } else {
        handleOutcomeFailure(listed);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [client, handleOutcomeFailure, redirectToTerms, session]);

  async function handleLogout() {
    if (loggingOut.current) return;
    loggingOut.current = true;
    await logout(client, tokenStorage);
    loggingOut.current = false;
    onLoggedOut?.();
    navigate("/login");
  }

  async function handleRevoke(sessionId: number) {
    setRevokingId(sessionId);
    setErrorKey(null);
    const result = await revokeSession(client, sessionId);
    setRevokingId(null);
    if (result.kind === "ok") {
      setSessions((current) => current.filter((item) => item.id !== sessionId));
    } else {
      handleOutcomeFailure(result);
    }
  }

  async function handleRevokeOthers() {
    setRevokingOthers(true);
    setErrorKey(null);
    const result = await revokeOtherSessions(client);
    setRevokingOthers(false);
    if (result.kind === "ok") {
      setSessions((current) => current.filter((item) => item.is_current));
    } else {
      handleOutcomeFailure(result);
    }
  }

  const navItems: SidebarItem[] = [
    { id: "home", label: t("auth.homeTitle"), href: "/", icon: <IconHouse /> },
  ];

  const columns: TableColumn[] = [
    { key: "ip", header: t("auth.colIp"), kind: "code" },
    { key: "userAgent", header: t("auth.colUserAgent") },
    { key: "createdAt", header: t("auth.colCreatedAt"), kind: "code" },
    { key: "lastSeenAt", header: t("auth.colLastSeenAt"), kind: "code" },
    { key: "status", header: t("auth.colStatus") },
    { key: "action", header: t("auth.colAction") },
  ];

  const rows: TableRow[] = sessions.map((item) => ({
    id: String(item.id),
    cells: {
      ip: item.ip,
      userAgent: item.user_agent,
      createdAt: formatTimestamp(item.created_at, i18n.language),
      lastSeenAt: formatTimestamp(item.last_seen_at, i18n.language),
      status: item.is_current ? <Chip>{t("auth.currentSession")}</Chip> : t("auth.otherSession"),
      action: item.is_current ? null : (
        <IconButton
          label={t("auth.revokeSession")}
          icon={<IconLogOut />}
          tooltipAlign="end"
          processing={revokingId === item.id}
          onClick={() => void handleRevoke(item.id)}
        />
      ),
    },
  }));

  const otherCount = sessions.filter((item) => !item.is_current).length;

  return (
    <AppLayout
      items={navItems}
      activeId="home"
      user={
        user
          ? {
              name: user.name || user.email,
              initials: userInitials(user),
              menu: [
                {
                  id: "logout",
                  label: t("auth.logout"),
                  icon: <IconLogOut />,
                  onSelect: () => void handleLogout(),
                },
              ],
            }
          : undefined
      }
      storage={storage}
    >
      <h1>{t("auth.homeTitle")}</h1>
      {errorKey && <FormMessage type="error" messageKey={errorKey as never} />}
      <Block
        as="section"
        title={t("auth.sessionsTitle")}
        count={sessions.length}
        actions={
          <Button
            variant="secondary"
            disabled={otherCount === 0}
            processing={revokingOthers}
            onClick={() => void handleRevokeOthers()}
          >
            {t("auth.revokeOthers")}
          </Button>
        }
      >
        <Table
          label={t("auth.sessionsTitle")}
          columns={columns}
          rows={rows}
          emptyMessage={t("auth.sessionsEmpty")}
        />
      </Block>
    </AppLayout>
  );
}
