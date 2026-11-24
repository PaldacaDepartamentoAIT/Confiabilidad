import { useEffect, useId, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { acceptTerms, getSession, logout, type SessionInfo } from "../api/auth";
import type { ApiClient, TermsStatus } from "../api/client";
import type { LegalDocument } from "../api/registration";
import { Button } from "../components/Button";
import { FormMessage } from "../components/FormMessage";
import { DocumentCheckbox } from "../components/fields/DocumentCheckbox";
import { RequiredLegend } from "../components/fields/RequiredLegend";
import { useFormValidation, type FieldError, type Validator } from "../forms/useFormValidation";
import type { LanguageStorage } from "../i18n/language";
import { PublicLayout } from "../layouts/PublicLayout";
import { PublicPage } from "../layouts/PublicPage";
import { translateCode } from "../registration/serverErrors";
import { navigate } from "../routing/router";
import type { TokenStorage } from "./tokenStorage";

const mustAccept: Validator = (value) => (value ? null : { key: "termsNotAccepted" });
const FIELDS = { terms: [mustAccept] };

type TermsPageProps = {
  client: ApiClient;
  session?: SessionInfo | null;
  storage?: LanguageStorage;
  tokenStorage?: TokenStorage;
  onAccepted?: () => void;
  onLoggedOut?: () => void;
};

export function TermsPage({
  client,
  session,
  storage,
  tokenStorage,
  onAccepted,
  onLoggedOut,
}: TermsPageProps) {
  const { t, i18n } = useTranslation();
  const titleId = useId();
  const initialLang = useRef(i18n.language);
  const [loadedSession, setLoadedSession] = useState<SessionInfo | null>(session ?? null);
  const [processing, setProcessing] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const { allErrors, onBlur, handleSubmit, showResult, message, formRef, messageRef } =
    useFormValidation(FIELDS, { processing });

  useEffect(() => {
    if (session !== undefined) setLoadedSession(session);
  }, [session]);

  useEffect(() => {
    const languageChanged = initialLang.current !== i18n.language;
    if (session !== undefined && !languageChanged) return;
    initialLang.current = i18n.language;
    let active = true;
    void getSession(client).then((result) => {
      if (!active) return;
      if (result.kind === "ok") setLoadedSession(result.data);
      else if (result.kind === "unauthenticated") {
        onLoggedOut?.();
        navigate("/login");
      }
    });
    return () => {
      active = false;
    };
  }, [client, i18n.language, onLoggedOut, session]);

  const termsStatus: TermsStatus = loadedSession?.terms_status ?? "no_current_version";
  const terms: LegalDocument | null = loadedSession?.terms ?? null;
  const canAccept = termsStatus === "not_accepted" && terms !== null;

  async function send() {
    if (!terms) return;
    setProcessing(true);
    const result = await acceptTerms(client, { version: terms.version, locale: terms.locale });
    setProcessing(false);
    if (result.kind === "ok") {
      onAccepted?.();
      navigate("/");
    } else if (result.kind === "unauthenticated") {
      onLoggedOut?.();
      navigate("/login");
    } else if (result.kind === "fieldErrors") {
      const code = result.errors.non_field_errors?.[0] ?? result.errors.terms?.[0] ?? "invalid";
      showResult({
        message: { type: "error", messageKey: `validation.${translateCode(code).key}` },
      });
    } else if (result.kind === "refused") {
      showResult({
        message: { type: "error", messageKey: `validation.${translateCode(result.code).key}` },
      });
    } else if (result.kind === "networkError") {
      showResult({ message: { type: "error", messageKey: "validation.networkError" } });
    } else {
      showResult({ message: { type: "error", messageKey: "validation.serverError" } });
    }
  }

  async function handleLogout() {
    setLoggingOut(true);
    await logout(client, tokenStorage);
    setLoggingOut(false);
    onLoggedOut?.();
    navigate("/login");
  }

  const errorText = (list: readonly FieldError[] | undefined) =>
    list?.map((error) => t(`validation.${error.key}`, error.params)).join(" ") || undefined;

  return (
    <PublicLayout storage={storage}>
      <PublicPage title={t("auth.termsTitle")} titleId={titleId}>
        {canAccept && terms ? (
          <>
            <p>{t("auth.termsIntro")}</p>
            <RequiredLegend />
            {message && (
              <FormMessage ref={messageRef} type={message.type} messageKey={message.messageKey} />
            )}
            <form
              ref={formRef}
              aria-labelledby={titleId}
              noValidate
              onSubmit={handleSubmit(() => void send())}
            >
              <DocumentCheckbox
                label={t("auth.termsLabel")}
                document={terms.content}
                name="terms"
                required
                error={errorText(allErrors.terms)}
                onBlur={onBlur("terms")}
              />
              <Button type="submit" keepFocusOnMouseDown processing={processing}>
                {t("auth.termsSubmit")}
              </Button>
            </form>
          </>
        ) : (
          <FormMessage type="error" messageKey="auth.termsUnavailableNotice" />
        )}
        <Button variant="secondary" processing={loggingOut} onClick={() => void handleLogout()}>
          {t("auth.logout")}
        </Button>
      </PublicPage>
    </PublicLayout>
  );
}
