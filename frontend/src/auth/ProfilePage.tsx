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

  useEffect(() => {
    const goTerms = (termsStatus: TermsStatus) => {
      onTermsRequired?.(termsStatus);
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
        onLoggedOut?.();
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
  }, [client, onLoggedOut, onTermsRequired, session, tokenStorage]);

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
      {loadError && <FormMessage type="error" messageKey={loadError} />}
      {profile && (
        <div className="profile-blocks">
          <Block as="section" title={t("auth.profileInfoTitle")}>
            <div className="profile-grid">
              <div className="full">
                <TextField label={t("auth.emailLabel")} value={profile.email} readOnly />
              </div>
              <TextField label={t("register.nameLabel")} value={profile.name} readOnly />
              <TextField
                label={t("register.birthdateLabel")}
                type="date"
                value={profile.birthdate}
                readOnly
              />
              <div className="full">
                <TextField label={t("register.countryLabel")} value={countryLabel} readOnly />
              </div>
            </div>
          </Block>
        </div>
      )}
    </AppLayout>
  );
}
