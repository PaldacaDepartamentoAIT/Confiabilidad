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
import { Chip } from "../components/Chip";
import { FormMessage } from "../components/FormMessage";
import { IconButton } from "../components/IconButton";
import { Table, type TableColumn, type TableRow } from "../components/data/Table";
import type { LanguageStorage } from "../i18n/language";
import { IconLogOut } from "../icons";
import { AppLayout } from "../layouts/AppLayout";
import { translateCode } from "../registration/serverErrors";
import { navigate } from "../routing/router";
import { privateNavItems, privateSidebarUser } from "./privateNav";
import type { TokenStorage } from "./tokenStorage";

type HomePageProps = {
  client: ApiClient;
  session?: SessionInfo | null;
  storage?: LanguageStorage;
  tokenStorage?: TokenStorage;
  onLoggedOut?: () => void;
  onTermsRequired?: (termsStatus: TermsStatus) => void;
  onSessionLoaded?: (session: SessionInfo) => void;
};

function formatTimestamp(iso: string, language: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return new Intl.DateTimeFormat(language, { dateStyle: "short", timeStyle: "short" }).format(
    parsed,
  );
}

export function HomePage({
  client,
  session,
  storage,
  tokenStorage,
  onLoggedOut,
  onTermsRequired,
  onSessionLoaded,
}: HomePageProps) {
  const { t, i18n } = useTranslation();
  const [user, setUser] = useState<AuthenticatedUser | null>(session?.user ?? null);
  const [sessions, setSessions] = useState<ActiveSessionItem[]>([]);
  const [sessionsLoaded, setSessionsLoaded] = useState(false);
  const [selectedIds, setSelectedIds] = useState<ReadonlySet<string>>(new Set());
  const [errorKey, setErrorKey] = useState<string | null>(null);
  const loggingOut = useRef(false);
  const [revokingSelected, setRevokingSelected] = useState(false);
  const onSessionLoadedRef = useRef(onSessionLoaded);
  onSessionLoadedRef.current = onSessionLoaded;

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
      if (result.kind === "unauthenticated") return redirectToLogin();
      if (result.kind === "termsRequired") {
        return redirectToTerms(result.termsStatus ?? "not_accepted");
      }
      if (result.kind === "refused" && result.code) {
        setErrorKey(`validation.${translateCode(result.code).key}`);
      } else {
        setErrorKey(
          result.kind === "networkError" ? "validation.networkError" : "validation.serverError",
        );
      }
    },
    [redirectToLogin, redirectToTerms],
  );

  useEffect(() => {
    let active = true;
    async function load() {
      let current = session;
      if (!current) {
        const info = await getSession(client);
        if (!active) return;
        if (info.kind !== "ok") return handleOutcomeFailure(info);
        current = info.data;
        onSessionLoadedRef.current?.(current);
      }
      setUser(current.user);
      if (current.terms_status !== "accepted") return redirectToTerms(current.terms_status);
      const listed = await listSessions(client);
      if (!active) return;
      if (listed.kind === "ok") {
        setErrorKey(null);
        setSessions(listed.data.sessions);
        setSessionsLoaded(true);
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

  const otherIdSet = new Set(
    sessions.filter((item) => !item.is_current).map((item) => String(item.id)),
  );

  async function handleRevokeSelected() {
    const targets = [...selectedIds].filter((id) => otherIdSet.has(id));
    if (targets.length === 0) return;
    setRevokingSelected(true);
    setErrorKey(null);

    if (targets.length === otherIdSet.size && targets.length > 1) {
      const result = await revokeOtherSessions(client);
      setRevokingSelected(false);
      if (result.kind !== "ok") return handleOutcomeFailure(result);
      setSessions((current) => current.filter((item) => item.is_current));
      setSelectedIds(new Set());
      return;
    }

    const removed = new Set<string>();
    let failure: { kind: string; termsStatus?: TermsStatus; code?: string } | null = null;
    for (const id of targets) {
      const result = await revokeSession(client, Number(id));
      if (result.kind === "ok") removed.add(id);
      else {
        failure = result;
        break;
      }
    }
    setRevokingSelected(false);
    if (removed.size > 0) {
      setSessions((current) => current.filter((item) => !removed.has(String(item.id))));
      setSelectedIds((current) => new Set([...current].filter((id) => !removed.has(id))));
    }
    if (failure) handleOutcomeFailure(failure);
  }

  const columns: TableColumn[] = [
    { key: "ip", header: t("auth.colIp"), kind: "code" },
    { key: "userAgent", header: t("auth.colUserAgent") },
    { key: "createdAt", header: t("auth.colCreatedAt"), kind: "code" },
    { key: "lastSeenAt", header: t("auth.colLastSeenAt"), kind: "code" },
    { key: "status", header: t("auth.colStatus") },
  ];

  const rows: TableRow[] = sessions.map((item) => ({
    id: String(item.id),
    cells: {
      ip: item.ip,
      userAgent: item.user_agent,
      createdAt: formatTimestamp(item.created_at, i18n.language),
      lastSeenAt: formatTimestamp(item.last_seen_at, i18n.language),
      status: item.is_current ? <Chip>{t("auth.currentSession")}</Chip> : t("auth.otherSession"),
    },
  }));

  const sessionsPending = !sessionsLoaded && !errorKey;

  return (
    <AppLayout
      items={privateNavItems(t)}
      activeId="home"
      user={privateSidebarUser(user, t, () => void handleLogout())}
      storage={storage}
    >
      <div className="page-head">
        <h1>{t("auth.homeTitle")}</h1>
        <div className={user ? "skel-slot is-ready" : "skel-slot is-loading"}>
          <p className="skel-content">
            {user
              ? user.name
                ? t("auth.signedInAs", { name: user.name, email: user.email })
                : user.email
              : "\u00a0"}
          </p>
          <span className="skeleton skel-mask skel-line" aria-hidden="true" />
        </div>
      </div>
      {errorKey && <FormMessage type="error" messageKey={errorKey as never} />}
      <Block
        as="section"
        title={t("auth.sessionsTitle")}
        count={sessionsLoaded ? sessions.length : undefined}
        aria-busy={sessionsPending}
      >
        <div className={sessionsPending ? "skel-slot is-loading" : "skel-slot is-ready"}>
          <div className="skel-content">
            <Table
              label={t("auth.sessionsTitle")}
              columns={columns}
              rows={rows}
              emptyMessage={t("auth.sessionsEmpty")}
              selection={{
                selectedIds,
                onChange: setSelectedIds,
                isSelectable: (row) => otherIdSet.has(row.id),
                selectAllLabel: t("auth.revokeOthers"),
                rowLabel: (row) =>
                  t("auth.selectSession", { agent: String(row.cells.userAgent ?? row.id) }),
                selectedLabel: (count) =>
                  count === 1 ? t("auth.selectedOne") : t("auth.selectedMany", { count }),
                actions: (
                  <IconButton
                    size="sm"
                    label={t("auth.revokeSession")}
                    icon={<IconLogOut />}
                    tooltipAlign="end"
                    processing={revokingSelected}
                    onClick={() => void handleRevokeSelected()}
                  />
                ),
              }}
            />
          </div>
          <div className="skel-mask skel-rows" aria-hidden="true">
            <div className="skeleton skel-row" />
            <div className="skeleton skel-row" />
          </div>
        </div>
      </Block>
    </AppLayout>
  );
}
