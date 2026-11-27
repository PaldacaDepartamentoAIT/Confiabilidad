import type { ParseKeys } from "i18next";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { logout, type AuthenticatedUser, type SessionInfo } from "../api/auth";
import type { ApiClient, ApiResult, TermsStatus } from "../api/client";
import {
  changePassword,
  disableAccount,
  getProfile,
  markAccountDisabledNotice,
  updateProfile,
  type DisableBlockReason,
  type ProfileData,
  type ProfileUpdate,
} from "../api/profile";
import { fetchOptions } from "../api/registration";
import { Block } from "../components/Block";
import { Button } from "../components/Button";
import { FormMessage } from "../components/FormMessage";
import { IconButton } from "../components/IconButton";
import { Notice } from "../components/Notice";
import { PasswordField } from "../components/fields/PasswordField";
import { RequiredLegend } from "../components/fields/RequiredLegend";
import { SelectField, type SelectOption } from "../components/fields/SelectField";
import { TextField } from "../components/fields/TextField";
import { Menu } from "../components/menu/Menu";
import { useToast } from "../components/toast/toastContext";
import { countryOptions } from "../forms/countries";
import { newPasswordRules } from "../forms/passwordRules";
import {
  useFormValidation,
  type FieldError,
  type SubmitResult,
  type Validator,
} from "../forms/useFormValidation";
import type { LanguageStorage } from "../i18n/language";
import { IconMoreVertical } from "../icons";
import { AppLayout } from "../layouts/AppLayout";
import { translateCode, translateFieldErrors } from "../registration/serverErrors";
import { useCountdown } from "../registration/useCountdown";
import { navigate } from "../routing/router";
import { required } from "../showcase/validators";
import { privateNavItems, privateSidebarUser, usePrivateUser } from "./privateNav";
import type { TokenStorage } from "./tokenStorage";
import "./ProfilePage.css";

const FIELDS = { name: [required], birthdate: [required], country: [] };
type Field = keyof typeof FIELDS;

const PASSWORD_FIELDS = {
  current_password: [required],
  new_password: [required, ...newPasswordRules],
};
type PasswordFieldName = keyof typeof PASSWORD_FIELDS;

const DISABLE_FIELDS = { current_password: [required] };
type DisableFieldName = keyof typeof DISABLE_FIELDS;
type CardMode = "view" | "edit" | "password" | "disable";

function fieldResult<Name extends string>(
  errors: Record<string, string[]>,
  fields: Record<Name, readonly Validator[]>,
): SubmitResult<Name> {
  const known = Object.keys(errors).every((name) => name in fields);
  const nonField = errors.non_field_errors?.[0];
  const message = nonField
    ? ({ type: "error", messageKey: `validation.${translateCode(nonField).key}` } as const)
    : known
      ? undefined
      : ({ type: "error", messageKey: "validation.unknownError" } as const);
  const translated = translateFieldErrors(errors);
  const fieldErrors: Partial<Record<Name, FieldError[]>> = {};
  for (const name of Object.keys(fields) as Name[]) {
    if (translated[name]) fieldErrors[name] = translated[name];
  }
  return { fieldErrors, message };
}

function handleFailure<Name extends string>(
  result: Exclude<ApiResult<unknown>, { kind: "ok" }>,
  fields: Record<Name, readonly Validator[]>,
  showResult: (result: SubmitResult<Name>) => void,
  onUnauthenticated: () => void,
  onTermsRequired: (status: TermsStatus) => void,
) {
  if (result.kind === "unauthenticated") return onUnauthenticated();
  if (result.kind === "termsRequired") return onTermsRequired(result.termsStatus);
  if (result.kind === "fieldErrors") return showResult(fieldResult(result.errors, fields));
  if (result.kind === "networkError") {
    return showResult({ message: { type: "error", messageKey: "validation.networkError" } });
  }
  if (result.kind === "refused") {
    return showResult({
      message: { type: "error", messageKey: `validation.${translateCode(result.code).key}` },
    });
  }
  showResult({ message: { type: "error", messageKey: "validation.serverError" } });
}

function useErrorText() {
  const { t } = useTranslation();
  return (list: readonly FieldError[] | undefined) =>
    list?.map((error) => t(`validation.${error.key}`, error.params)).join(" ") || undefined;
}

type ProfilePageProps = {
  client: ApiClient;
  session?: SessionInfo | null;
  storage?: LanguageStorage;
  tokenStorage?: TokenStorage;
  onLoggedOut?: () => void;
  onTermsRequired?: (termsStatus: TermsStatus) => void;
  onProfileUpdated?: (user: AuthenticatedUser) => void;
};

function ProfileSkeleton() {
  const { t } = useTranslation();
  const rowLabels = [
    t("register.nameLabel"),
    t("register.countryLabel"),
    t("register.birthdateLabel"),
  ];
  return (
    <div className="profile-form">
      <div className="fld">
        <span className="lbl">{t("auth.emailLabel")}</span>
        <div className="skeleton skel-field" />
      </div>
      <div className="profile-grid">
        {rowLabels.map((label) => (
          <div key={label} className="fld">
            <span className="lbl">{label}</span>
            <div className="skeleton skel-field" />
          </div>
        ))}
      </div>
    </div>
  );
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
  const { t, i18n } = useTranslation();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [countryCodes, setCountryCodes] = useState<string[]>([]);
  const [loadError, setLoadError] = useState<ParseKeys | null>(null);
  const [mode, setMode] = useState<CardMode>("view");
  const passwordWait = useCountdown();
  const disableWait = useCountdown();
  const { start: startDisableWait } = disableWait;
  const loggingOut = useRef(false);
  const { notify } = useToast();
  const { user: ctxUser, setUser: setCtxUser, collapsed, setCollapsed } = usePrivateUser();
  const cbRef = useRef({ onLoggedOut, onTermsRequired, setCtxUser });
  cbRef.current = { onLoggedOut, onTermsRequired, setCtxUser };

  const goLogin = useCallback(() => {
    tokenStorage?.clear();
    cbRef.current.setCtxUser(null);
    cbRef.current.onLoggedOut?.();
    navigate("/login");
  }, [tokenStorage]);

  const goTerms = useCallback((status: TermsStatus) => {
    cbRef.current.onTermsRequired?.(status);
    navigate("/terms");
  }, []);

  useEffect(() => {
    if (session && session.terms_status !== "accepted") return goTerms(session.terms_status);
    let active = true;
    void Promise.all([getProfile(client), fetchOptions(client)]).then(([prof, opts]) => {
      if (!active) return;
      if (prof.kind === "unauthenticated") return goLogin();
      if (prof.kind === "termsRequired") return goTerms(prof.termsStatus);
      if (prof.kind !== "ok" || opts.kind !== "ok") {
        const err = prof.kind !== "ok" ? prof : opts;
        return setLoadError(
          err.kind === "networkError" ? "validation.networkError" : "validation.serverError",
        );
      }
      setLoadError(null);
      setProfile(prof.data);
      setCountryCodes(opts.data.countries);
      cbRef.current.setCtxUser({ email: prof.data.email, name: prof.data.name });
      if (prof.data.disable_retry_after && prof.data.disable_retry_after > 0) {
        startDisableWait(prof.data.disable_retry_after);
      }
    });
    return () => {
      active = false;
    };
  }, [client, goLogin, goTerms, session, startDisableWait]);

  async function handleLogout() {
    if (loggingOut.current) return;
    loggingOut.current = true;
    await logout(client, tokenStorage);
    loggingOut.current = false;
    setCtxUser(null);
    onLoggedOut?.();
    navigate("/login");
  }

  const countries = useMemo(
    () => countryOptions(countryCodes, i18n.language),
    [countryCodes, i18n.language],
  );

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
          <Block
            as="section"
            title={
              mode === "password"
                ? t("auth.passwordChangeTitle")
                : mode === "disable"
                  ? t("auth.disableAccountTitle")
                  : t("auth.profileInfoTitle")
            }
            loading={profile === null}
            loadingContent={mode === "view" ? <ProfileSkeleton /> : undefined}
            actions={
              profile && (
                <div className="profile-menu">
                  <Menu
                    label={t("auth.profileActions")}
                    align="right"
                    selectable={false}
                    options={[
                      { value: "edit", label: t("auth.profileEdit") },
                      { value: "password", label: t("auth.profileChangePassword") },
                      { value: "disable", label: t("auth.profileDisable") },
                    ]}
                    onSelect={(action) => {
                      if (action === "edit" || action === "password" || action === "disable") {
                        setMode(action);
                      }
                    }}
                    renderTrigger={(triggerProps) => (
                      <IconButton
                        {...triggerProps}
                        size="sm"
                        tooltipAlign="end"
                        label={t("auth.profileActions")}
                        icon={<IconMoreVertical />}
                      />
                    )}
                  />
                </div>
              )
            }
          >
            {profile &&
              (mode === "password" ? (
                <PasswordChangeBlock
                  client={client}
                  wait={passwordWait}
                  onCancel={() => setMode("view")}
                  onSaved={() => {
                    setMode("view");
                    notify({ kind: "success", message: t("auth.passwordChanged") });
                  }}
                  onUnauthenticated={goLogin}
                  onTermsRequired={goTerms}
                />
              ) : mode === "disable" ? (
                <DisableAccountBlock
                  client={client}
                  profile={profile}
                  wait={disableWait}
                  onCancel={() => setMode("view")}
                  onBlocked={(reason) =>
                    setProfile((cur) =>
                      cur ? { ...cur, can_disable: false, disable_block_reason: reason } : cur,
                    )
                  }
                  onDisabled={() => {
                    markAccountDisabledNotice();
                    goLogin();
                  }}
                  onUnauthenticated={goLogin}
                  onTermsRequired={goTerms}
                />
              ) : (
                <PersonalInfoBlock
                  key={mode === "edit" ? "edit" : "view"}
                  client={client}
                  profile={profile}
                  countries={countries}
                  editing={mode === "edit"}
                  onCancel={() => setMode("view")}
                  onSaved={(updated) => {
                    const next = { email: updated.email, name: updated.name };
                    setProfile(updated);
                    setCtxUser(next);
                    onProfileUpdated?.(next);
                    setMode("view");
                    notify({ kind: "success", message: t("auth.profileSaved") });
                  }}
                  onUnauthenticated={goLogin}
                  onTermsRequired={goTerms}
                />
              ))}
          </Block>
        </div>
      )}
    </AppLayout>
  );
}

function PersonalInfoBlock({
  client,
  profile,
  countries,
  editing,
  onCancel,
  onSaved,
  onUnauthenticated,
  onTermsRequired,
}: {
  client: ApiClient;
  profile: ProfileData;
  countries: readonly SelectOption[];
  editing: boolean;
  onCancel: () => void;
  onSaved: (updated: ProfileData) => void;
  onUnauthenticated: () => void;
  onTermsRequired: (status: TermsStatus) => void;
}) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const [processing, setProcessing] = useState(false);
  const { allErrors, onBlur, handleSubmit, showResult, message, formRef, messageRef } =
    useFormValidation(FIELDS, { scrollToError: true, processing });

  async function send(values: Record<Field, string>) {
    if (!editing) return;
    if (profile.country !== "ZZ" && !values.country) {
      return showResult({ fieldErrors: { country: { key: "countryInvalid" } } });
    }
    const payload: ProfileUpdate = { name: values.name, birthdate: values.birthdate };
    if (values.country) payload.country = values.country;
    setProcessing(true);
    const result = await updateProfile(client, payload);
    setProcessing(false);
    if (result.kind === "ok") {
      showResult({});
      onSaved(result.data);
    } else handleFailure(result, FIELDS, showResult, onUnauthenticated, onTermsRequired);
  }

  const countryLabel =
    profile.country === "ZZ"
      ? t("auth.profileCountryUnassigned")
      : (countries.find((item) => item.value === profile.country)?.label ?? profile.country);

  return (
    <>
      {editing && message && (
        <FormMessage ref={messageRef} type={message.type} messageKey={message.messageKey} />
      )}
      <form
        ref={formRef}
        className="profile-form"
        noValidate
        onSubmit={handleSubmit((values) => void send(values))}
      >
        <TextField label={t("auth.emailLabel")} type="email" value={profile.email} disabled />
        <div className="profile-grid">
          <TextField
            label={t("register.nameLabel")}
            name={editing ? "name" : undefined}
            autoComplete="name"
            required={editing}
            readOnly={!editing}
            value={editing ? undefined : profile.name}
            defaultValue={editing ? profile.name : undefined}
            error={editing ? errorText(allErrors.name) : undefined}
            onBlur={editing ? onBlur("name") : undefined}
          />
          {editing ? (
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
          ) : (
            <TextField label={t("register.countryLabel")} value={countryLabel} readOnly />
          )}
          <TextField
            label={t("register.birthdateLabel")}
            name={editing ? "birthdate" : undefined}
            type="date"
            autoComplete="bday"
            required={editing}
            readOnly={!editing}
            value={editing ? undefined : profile.birthdate}
            defaultValue={editing ? profile.birthdate : undefined}
            error={editing ? errorText(allErrors.birthdate) : undefined}
            onBlur={editing ? onBlur("birthdate") : undefined}
          />
        </div>
        {editing && (
          <>
            <div className="profile-actions">
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  showResult({});
                  onCancel();
                }}
              >
                {t("auth.profileCancel")}
              </Button>
              <Button type="submit" keepFocusOnMouseDown processing={processing}>
                {t("auth.profileSave")}
              </Button>
            </div>
            <RequiredLegend />
          </>
        )}
      </form>
    </>
  );
}

function PasswordChangeBlock({
  client,
  wait,
  onCancel,
  onSaved,
  onUnauthenticated,
  onTermsRequired,
}: {
  client: ApiClient;
  wait: ReturnType<typeof useCountdown>;
  onCancel: () => void;
  onSaved: () => void;
  onUnauthenticated: () => void;
  onTermsRequired: (status: TermsStatus) => void;
}) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const [processing, setProcessing] = useState(false);
  const { allErrors, onBlur, handleSubmit, showResult, message, formRef, messageRef } =
    useFormValidation(PASSWORD_FIELDS, { scrollToError: true, processing });

  async function send(values: Record<PasswordFieldName, string>) {
    if (wait.remaining > 0) return;
    setProcessing(true);
    const result = await changePassword(client, values);
    setProcessing(false);
    if (result.kind === "ok") {
      formRef.current?.reset();
      showResult({});
      return onSaved();
    }
    if (result.kind === "rateLimited") return wait.start(result.retryAfter);
    if (result.kind === "fieldErrors" && "current_password" in result.errors) {
      const currentInput = formRef.current?.elements.namedItem("current_password");
      if (currentInput instanceof HTMLInputElement) currentInput.value = "";
    }
    handleFailure(result, PASSWORD_FIELDS, showResult, onUnauthenticated, onTermsRequired);
  }

  return (
    <>
      {message && (
        <FormMessage ref={messageRef} type={message.type} messageKey={message.messageKey} />
      )}
      <form
        ref={formRef}
        className="profile-form"
        noValidate
        onSubmit={handleSubmit((values) => void send(values))}
      >
        <div className="profile-password-grid">
          <PasswordField
            label={t("auth.currentPasswordLabel")}
            name="current_password"
            kind="current"
            required
            error={errorText(allErrors.current_password)}
            onBlur={onBlur("current_password")}
          />
          <PasswordField
            label={t("auth.newPasswordLabel")}
            name="new_password"
            kind="new"
            required
            error={errorText(allErrors.new_password)}
            onBlur={onBlur("new_password")}
          />
        </div>
        <div className="profile-actions">
          {wait.remaining > 0 && (
            <p className="profile-wait" role="status">
              {t("validation.retryIn", { seconds: wait.remaining })}
            </p>
          )}
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              formRef.current?.reset();
              showResult({});
              onCancel();
            }}
          >
            {t("auth.profileCancel")}
          </Button>
          <Button
            type="submit"
            keepFocusOnMouseDown
            processing={processing}
            disabled={wait.remaining > 0}
          >
            {t("auth.passwordChangeSubmit")}
          </Button>
        </div>
        <RequiredLegend />
      </form>
    </>
  );
}

function DisableAccountBlock({
  client,
  profile,
  wait,
  onCancel,
  onBlocked,
  onDisabled,
  onUnauthenticated,
  onTermsRequired,
}: {
  client: ApiClient;
  profile: ProfileData;
  wait: ReturnType<typeof useCountdown>;
  onCancel: () => void;
  onBlocked: (reason: DisableBlockReason) => void;
  onDisabled: () => void;
  onUnauthenticated: () => void;
  onTermsRequired: (status: TermsStatus) => void;
}) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const [step, setStep] = useState<1 | 2>(1);
  const [processing, setProcessing] = useState(false);
  const { allErrors, onBlur, handleSubmit, showResult, formRef } = useFormValidation(
    DISABLE_FIELDS,
    { scrollToError: true, processing },
  );

  const blockedReason =
    profile.disable_block_reason ?? (profile.can_disable === false ? "owns_company" : null);
  const blocked = blockedReason !== null;

  async function send(values: Record<DisableFieldName, string>) {
    if (wait.remaining > 0 || blocked) return;
    setProcessing(true);
    const result = await disableAccount(client, values);
    setProcessing(false);
    if (result.kind === "ok") {
      formRef.current?.reset();
      showResult({});
      return onDisabled();
    }
    if (result.kind === "rateLimited") return wait.start(result.retryAfter);
    if (result.kind === "fieldErrors" && "current_password" in result.errors) {
      const currentInput = formRef.current?.elements.namedItem("current_password");
      if (currentInput instanceof HTMLInputElement) currentInput.value = "";
    }
    if (
      result.kind === "refused" &&
      (result.code === "owns_company" || result.code === "last_superuser")
    ) {
      onBlocked(result.code);
      setStep(1);
    }
    handleFailure(result, DISABLE_FIELDS, showResult, onUnauthenticated, onTermsRequired);
  }

  if (step === 1 || blocked) {
    return (
      <div className="profile-disable">
        <p className="profile-intro">{t("auth.disableAccountIntro")}</p>
        {blocked && <Notice>{t(`validation.${translateCode(blockedReason).key}`)}</Notice>}
        <div className="profile-actions">
          {wait.remaining > 0 && (
            <p className="profile-wait" role="status">
              {t("validation.retryIn", { seconds: wait.remaining })}
            </p>
          )}
          <Button type="button" variant="secondary" onClick={onCancel}>
            {t("auth.profileCancel")}
          </Button>
          <Button type="button" disabled={blocked} onClick={() => setStep(2)}>
            {t("auth.disableAccountContinue")}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form
      ref={formRef}
      className="profile-form"
      noValidate
      onSubmit={handleSubmit((values) => void send(values))}
    >
      <p className="profile-intro">{t("auth.disableAccountConfirmPrompt")}</p>
      <PasswordField
        label={t("auth.currentPasswordLabel")}
        name="current_password"
        kind="current"
        required
        error={errorText(allErrors.current_password)}
        onBlur={onBlur("current_password")}
      />
      <div className="profile-actions">
        {wait.remaining > 0 && (
          <p className="profile-wait" role="status">
            {t("validation.retryIn", { seconds: wait.remaining })}
          </p>
        )}
        <Button
          type="button"
          variant="secondary"
          onClick={() => {
            formRef.current?.reset();
            showResult({});
            onCancel();
          }}
        >
          {t("auth.profileCancel")}
        </Button>
        <Button
          type="submit"
          keepFocusOnMouseDown
          processing={processing}
          disabled={wait.remaining > 0}
        >
          {t("auth.disableAccountSubmit")}
        </Button>
      </div>
      <RequiredLegend />
    </form>
  );
}
