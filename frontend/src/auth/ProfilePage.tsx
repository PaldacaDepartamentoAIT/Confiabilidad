import type { ParseKeys } from "i18next";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { logout, type SessionInfo } from "../api/auth";
import type { ApiClient, TermsStatus } from "../api/client";
import { getProfile, type ProfileData } from "../api/profile";
import { Block } from "../components/Block";
import { FormMessage } from "../components/FormMessage";
import { TextField } from "../components/fields/TextField";
import { countryOptions } from "../forms/countries";
import type { LanguageStorage } from "../i18n/language";
import { AppLayout } from "../layouts/AppLayout";
import { navigate } from "../routing/router";
import { privateNavItems, privateSidebarUser, usePrivateUser } from "./privateNav";
import type { TokenStorage } from "./tokenStorage";
import "./ProfilePage.css";

type ProfilePageProps = {
  client: ApiClient;
  session?: SessionInfo | null;
  storage?: LanguageStorage;
  tokenStorage?: TokenStorage;
  onLoggedOut?: () => void;
  onTermsRequired?: (termsStatus: TermsStatus) => void;
};

export function ProfilePage({
  client,
  session,
  storage,
  tokenStorage,
  onLoggedOut,
  onTermsRequired,
}: ProfilePageProps) {
  const { t, i18n } = useTranslation();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loadError, setLoadError] = useState<ParseKeys | null>(null);
  const loggingOut = useRef(false);
  const { user: ctxUser, setUser: setCtxUser, collapsed, setCollapsed } = usePrivateUser();
  const cbRef = useRef({ onLoggedOut, onTermsRequired, setCtxUser });
  cbRef.current = { onLoggedOut, onTermsRequired, setCtxUser };

  useEffect(() => {
    const goTerms = (status: TermsStatus) => {
      cbRef.current.onTermsRequired?.(status);
      navigate("/terms");
    };
    if (session && session.terms_status !== "accepted") return goTerms(session.terms_status);
    let active = true;
    void getProfile(client).then((res) => {
      if (!active) return;
      if (res.kind === "unauthenticated") {
        tokenStorage?.clear();
        cbRef.current.setCtxUser(null);
        cbRef.current.onLoggedOut?.();
        return navigate("/login");
      }
      if (res.kind === "termsRequired") return goTerms(res.termsStatus);
      if (res.kind !== "ok") {
        return setLoadError(
          res.kind === "networkError" ? "validation.networkError" : "validation.serverError",
        );
      }
      setLoadError(null);
      setProfile(res.data);
      cbRef.current.setCtxUser({ email: res.data.email, name: res.data.name });
    });
    return () => {
      active = false;
    };
  }, [client, session, tokenStorage]);

  async function handleLogout() {
    if (loggingOut.current) return;
    loggingOut.current = true;
    await logout(client, tokenStorage);
    loggingOut.current = false;
    setCtxUser(null);
    onLoggedOut?.();
    navigate("/login");
  }

  const countryLabel = profile
    ? profile.country === "ZZ"
      ? t("auth.profileCountryUnassigned")
      : (countryOptions([profile.country], i18n.language)[0]?.label ?? profile.country)
    : "";
  const loading = profile === null;
  const fields: readonly { label: string; value: string; type?: "date"; full?: boolean }[] = [
    { label: t("auth.emailLabel"), value: profile?.email ?? "", full: true },
    { label: t("register.nameLabel"), value: profile?.name ?? "" },
    { label: t("register.birthdateLabel"), value: profile?.birthdate ?? "", type: "date" },
    { label: t("register.countryLabel"), value: countryLabel, full: true },
  ];

  return (
    <AppLayout
      items={privateNavItems(t)}
      activeId="profile"
      user={privateSidebarUser(profile ?? session?.user ?? ctxUser, t, () => void handleLogout())}
      storage={storage}
      collapsed={collapsed}
      onCollapsedChange={setCollapsed}
    >
      <div className="page-head">
        <h1>{t("auth.profileTitle")}</h1>
      </div>
      {loadError ? (
        <FormMessage type="error" messageKey={loadError} />
      ) : (
        <div className="profile-blocks">
          <Block as="section" title={t("auth.profileInfoTitle")} aria-busy={loading}>
            <div className="profile-grid">
              {fields.map(({ label, value, type, full }) => (
                <div
                  key={label}
                  className={[full && "full", "skel-slot", loading ? "is-loading" : "is-ready"]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <div className="skel-content">
                    <TextField label={label} type={type} value={value} readOnly />
                  </div>
                  <div className="fld skel-mask" aria-hidden="true">
                    <span className="lbl">{label}</span>
                    <div className="skeleton skel-field" />
                  </div>
                </div>
              ))}
            </div>
          </Block>
        </div>
      )}
    </AppLayout>
  );
}
