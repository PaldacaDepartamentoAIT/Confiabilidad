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
import { privateNavItems, privateSidebarUser } from "./privateNav";
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
  const callbacksRef = useRef({ onLoggedOut, onTermsRequired });
  callbacksRef.current = { onLoggedOut, onTermsRequired };

  useEffect(() => {
    const goTerms = (termsStatus: TermsStatus) => {
      callbacksRef.current.onTermsRequired?.(termsStatus);
      navigate("/terms");
    };
    if (session && session.terms_status !== "accepted") {
      goTerms(session.terms_status);
      return;
    }
    let active = true;
    void getProfile(client).then((res) => {
      if (!active) return;
      if (res.kind === "unauthenticated") {
        tokenStorage?.clear();
        callbacksRef.current.onLoggedOut?.();
        navigate("/login");
        return;
      }
      if (res.kind === "termsRequired") return goTerms(res.termsStatus);
      if (res.kind !== "ok") {
        setLoadError(
          res.kind === "networkError" ? "validation.networkError" : "validation.serverError",
        );
        return;
      }
      setLoadError(null);
      setProfile(res.data);
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
      user={privateSidebarUser(profile ?? session?.user, t, () => void handleLogout())}
      storage={storage}
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
