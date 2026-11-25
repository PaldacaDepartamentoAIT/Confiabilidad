import type { ParseKeys } from "i18next";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { logout, type AuthenticatedUser, type SessionInfo } from "../api/auth";
import type { ApiClient, TermsStatus } from "../api/client";
import { getProfile, updateProfile, type ProfileData, type ProfileUpdate } from "../api/profile";
import { fetchOptions } from "../api/registration";
import { Block } from "../components/Block";
import { Button } from "../components/Button";
import { FormMessage } from "../components/FormMessage";
import { RequiredLegend } from "../components/fields/RequiredLegend";
import { SelectField } from "../components/fields/SelectField";
import { TextField } from "../components/fields/TextField";
import { countryOptions } from "../forms/countries";
import { useFormValidation, type FieldError, type SubmitResult } from "../forms/useFormValidation";
import type { LanguageStorage } from "../i18n/language";
import { IconHouse, IconInfo, IconLogOut } from "../icons";
import { AppLayout } from "../layouts/AppLayout";
import { translateCode, translateFieldErrors } from "../registration/serverErrors";
import { navigate } from "../routing/router";
import { required } from "../showcase/validators";
import type { TokenStorage } from "./tokenStorage";
import "./ProfilePage.css";

const FIELDS = { name: [required], birthdate: [required], country: [] };
type Field = keyof typeof FIELDS;

type ProfilePageProps = {
  client: ApiClient;
  session?: SessionInfo | null;
  storage?: LanguageStorage;
  tokenStorage?: TokenStorage;
  onLoggedOut?: () => void;
  onTermsRequired?: (termsStatus: TermsStatus) => void;
  onProfileUpdated?: (user: AuthenticatedUser) => void;
};

function userInitials(user: { name?: string; email: string } | null): string {
  const parts = (user?.name || user?.email || "U").trim().split(/\s+/);
  return (parts.length >= 2 ? `${parts[0][0]}${parts[1][0]}` : parts[0].slice(0, 2)).toUpperCase();
}

function fieldResult(errors: Record<string, string[]>): SubmitResult<Field> {
  const known = Object.keys(errors).every((name) => name in FIELDS);
  const nonField = errors.non_field_errors?.[0];
  const message = nonField
    ? ({ type: "error", messageKey: `validation.${translateCode(nonField).key}` } as const)
    : known
      ? undefined
      : ({ type: "error", messageKey: "validation.unknownError" } as const);
  return { fieldErrors: translateFieldErrors(errors), message };
}

export function ProfilePage({
  client,
  session,
  storage,
  tokenStorage,
  onLoggedOut,
  onTermsRequired,
  onProfileUpdated,
}: ProfilePageProps) {
  const { t } = useTranslation();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [countryCodes, setCountryCodes] = useState<string[]>([]);
  const [loadError, setLoadError] = useState<ParseKeys | null>(null);
  const loggingOut = useRef(false);

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

  useEffect(() => {
    if (session && session.terms_status !== "accepted") {
      redirectToTerms(session.terms_status);
      return;
    }
    let active = true;
    void Promise.all([getProfile(client), fetchOptions(client)]).then(([prof, opts]) => {
      if (!active) return;
      if (prof.kind === "unauthenticated") return redirectToLogin();
      if (prof.kind === "termsRequired") return redirectToTerms(prof.termsStatus);
      if (prof.kind !== "ok" || opts.kind !== "ok") {
        const err = prof.kind !== "ok" ? prof : opts;
        setLoadError(
          err.kind === "networkError" ? "validation.networkError" : "validation.serverError",
        );
        return;
      }
      setLoadError(null);
      setProfile(prof.data);
      setCountryCodes(opts.data.countries);
    });
    return () => {
      active = false;
    };
  }, [client, redirectToLogin, redirectToTerms, session]);

  async function handleLogout() {
    if (loggingOut.current) return;
    loggingOut.current = true;
    await logout(client, tokenStorage);
    loggingOut.current = false;
    onLoggedOut?.();
    navigate("/login");
  }

  const sidebarUser = profile ?? session?.user ?? null;

  return (
    <AppLayout
      items={[
        { id: "home", label: t("auth.homeTitle"), href: "/", icon: <IconHouse /> },
        { id: "profile", label: t("auth.profileNav"), href: "/profile", icon: <IconInfo /> },
      ]}
      activeId="profile"
      user={
        sidebarUser
          ? {
              name: sidebarUser.name || sidebarUser.email,
              initials: userInitials(sidebarUser),
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
      <div className="page-head">
        <h1>{t("auth.profileTitle")}</h1>
      </div>
      {loadError && <FormMessage type="error" messageKey={loadError} />}
      {profile && (
        <div className="profile-blocks">
          <PersonalInfoBlock
            client={client}
            profile={profile}
            countryCodes={countryCodes}
            onSaved={(updated) => {
              setProfile(updated);
              onProfileUpdated?.({ email: updated.email, name: updated.name });
            }}
            onUnauthenticated={redirectToLogin}
            onTermsRequired={redirectToTerms}
          />
        </div>
      )}
    </AppLayout>
  );
}

function PersonalInfoBlock({
  client,
  profile,
  countryCodes,
  onSaved,
  onUnauthenticated,
  onTermsRequired,
}: {
  client: ApiClient;
  profile: ProfileData;
  countryCodes: readonly string[];
  onSaved: (updated: ProfileData) => void;
  onUnauthenticated: () => void;
  onTermsRequired: (status: TermsStatus) => void;
}) {
  const { t, i18n } = useTranslation();
  const [processing, setProcessing] = useState(false);
  const { allErrors, onBlur, handleSubmit, showResult, message, formRef, messageRef } =
    useFormValidation(FIELDS, { scrollToError: true, processing });
  const countries = useMemo(
    () => countryOptions(countryCodes, i18n.language),
    [countryCodes, i18n.language],
  );

  async function send(values: Record<Field, string>) {
    if (profile.country !== "ZZ" && !values.country) {
      showResult({ fieldErrors: { country: { key: "countryInvalid" } } });
      return;
    }
    const payload: ProfileUpdate = { name: values.name, birthdate: values.birthdate };
    if (values.country) payload.country = values.country;
    setProcessing(true);
    const result = await updateProfile(client, payload);
    setProcessing(false);
    if (result.kind === "ok") {
      const nameInput = formRef.current?.elements.namedItem("name");
      if (nameInput instanceof HTMLInputElement) nameInput.value = result.data.name;
      onSaved(result.data);
      showResult({ message: { type: "success", messageKey: "auth.profileSaved" } });
    } else if (result.kind === "unauthenticated") onUnauthenticated();
    else if (result.kind === "termsRequired") onTermsRequired(result.termsStatus);
    else if (result.kind === "fieldErrors") showResult(fieldResult(result.errors));
    else if (result.kind === "networkError") {
      showResult({ message: { type: "error", messageKey: "validation.networkError" } });
    } else if (result.kind === "refused") {
      showResult({
        message: { type: "error", messageKey: `validation.${translateCode(result.code).key}` },
      });
    } else showResult({ message: { type: "error", messageKey: "validation.serverError" } });
  }

  const errorText = (list: readonly FieldError[] | undefined) =>
    list?.map((error) => t(`validation.${error.key}`, error.params)).join(" ") || undefined;

  return (
    <Block as="section" title={t("auth.profileInfoTitle")}>
      {message && (
        <FormMessage ref={messageRef} type={message.type} messageKey={message.messageKey} />
      )}
      <form
        ref={formRef}
        className="profile-form"
        noValidate
        onSubmit={handleSubmit((values) => void send(values))}
      >
        <div className="profile-grid">
          <div className="full">
            <TextField label={t("auth.emailLabel")} type="email" value={profile.email} readOnly />
          </div>
          <TextField
            label={t("register.nameLabel")}
            name="name"
            autoComplete="name"
            required
            defaultValue={profile.name}
            error={errorText(allErrors.name)}
            onBlur={onBlur("name")}
          />
          <TextField
            label={t("register.birthdateLabel")}
            name="birthdate"
            type="date"
            autoComplete="bday"
            required
            defaultValue={profile.birthdate}
            error={errorText(allErrors.birthdate)}
            onBlur={onBlur("birthdate")}
          />
          <div className="full">
            <SelectField
              label={t("register.countryLabel")}
              name="country"
              placeholder={
                profile.country === "ZZ"
                  ? t("auth.profileCountryUnassigned")
                  : t("register.countryPlaceholder")
              }
              options={countries}
              required={profile.country !== "ZZ"}
              defaultValue={profile.country === "ZZ" ? "" : profile.country}
              error={errorText(allErrors.country)}
              onBlur={onBlur("country")}
            />
          </div>
        </div>
        <div className="profile-actions">
          <Button type="submit" keepFocusOnMouseDown processing={processing}>
            {t("auth.profileSave")}
          </Button>
        </div>
        <RequiredLegend />
      </form>
    </Block>
  );
}
