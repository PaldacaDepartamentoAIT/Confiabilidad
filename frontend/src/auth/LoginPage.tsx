import { useId, useRef, useState, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";

import { login, type SessionInfo } from "../api/auth";
import type { ApiClient } from "../api/client";
import type { TokenStorage } from "./tokenStorage";
import { Button } from "../components/Button";
import { FormMessage } from "../components/FormMessage";
import { PasswordField } from "../components/fields/PasswordField";
import { RequiredLegend } from "../components/fields/RequiredLegend";
import { TextField } from "../components/fields/TextField";
import { useFormValidation, type FieldError, type SubmitResult } from "../forms/useFormValidation";
import type { LanguageStorage } from "../i18n/language";
import { PublicLayout } from "../layouts/PublicLayout";
import { PublicPage } from "../layouts/PublicPage";
import { translateCode, translateFieldErrors } from "../registration/serverErrors";
import { useCountdown } from "../registration/useCountdown";
import { navigate } from "../routing/router";
import { email, required } from "../showcase/validators";

const FIELDS = {
  email: [required, email],
  password: [required],
};

type Field = keyof typeof FIELDS;

const FAILURE = { type: "error", messageKey: "validation.serverError" } as const;
const NETWORK = { type: "error", messageKey: "validation.networkError" } as const;
const UNKNOWN = { type: "error", messageKey: "validation.unknownError" } as const;

function fieldResult(errors: Record<string, string[]>): SubmitResult<Field> {
  const known = Object.keys(errors).every((name) => name in FIELDS);
  return { fieldErrors: translateFieldErrors(errors), message: known ? undefined : UNKNOWN };
}

type LoginPageProps = {
  client: ApiClient;
  storage?: LanguageStorage;
  tokenStorage?: TokenStorage;
  onAuthenticated?: (session: SessionInfo) => void;
};

export function LoginPage({ client, storage, tokenStorage, onAuthenticated }: LoginPageProps) {
  const { t } = useTranslation();
  const titleId = useId();
  const passwordRef = useRef<HTMLInputElement>(null);
  const [processing, setProcessing] = useState(false);
  const wait = useCountdown();
  const { allErrors, onBlur, handleSubmit, showResult, message, formRef, messageRef } =
    useFormValidation(FIELDS, { scrollToError: true, processing });

  async function send(values: Record<Field, string>) {
    setProcessing(true);
    const result = await login(client, values, tokenStorage);
    setProcessing(false);
    if (result.kind === "ok") {
      onAuthenticated?.(result.data);
      navigate(result.data.terms_status === "accepted" ? "/" : "/terms");
    } else if (result.kind === "fieldErrors") {
      showResult(fieldResult(result.errors));
    } else if (result.kind === "rateLimited") {
      wait.start(result.retryAfter);
    } else if (result.kind === "refused") {
      if (result.code === "invalid_credentials" && passwordRef.current) {
        passwordRef.current.value = "";
      }
      const { key } = translateCode(result.code);
      showResult({ message: { type: "error", messageKey: `validation.${key}` } });
    } else if (result.kind === "networkError") {
      showResult({ message: NETWORK });
    } else {
      showResult({ message: FAILURE });
    }
  }

  function goToRegister(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    navigate("/register");
  }

  const errorText = (list: readonly FieldError[] | undefined) =>
    list?.map((error) => t(`validation.${error.key}`, error.params)).join(" ") || undefined;

  return (
    <PublicLayout storage={storage}>
      <PublicPage title={t("auth.loginTitle")} titleId={titleId}>
        <RequiredLegend />
        {wait.remaining > 0 && (
          <p role="status">{t("validation.retryIn", { seconds: wait.remaining })}</p>
        )}
        {message && (
          <FormMessage ref={messageRef} type={message.type} messageKey={message.messageKey} />
        )}
        <form
          ref={formRef}
          aria-labelledby={titleId}
          noValidate
          onSubmit={handleSubmit((values) => void send(values))}
        >
          <TextField
            label={t("auth.emailLabel")}
            name="email"
            type="email"
            autoComplete="email"
            required
            error={errorText(allErrors.email)}
            onBlur={onBlur("email")}
          />
          <PasswordField
            ref={passwordRef}
            label={t("auth.passwordLabel")}
            name="password"
            kind="current"
            required
            error={errorText(allErrors.password)}
            onBlur={onBlur("password")}
          />
          <Button
            type="submit"
            keepFocusOnMouseDown
            processing={processing}
            disabled={wait.remaining > 0}
          >
            {t("auth.loginSubmit")}
          </Button>
        </form>
        <p>
          <a href="/register" onClick={goToRegister}>
            {t("auth.createAccountLink")}
          </a>
        </p>
      </PublicPage>
    </PublicLayout>
  );
}
