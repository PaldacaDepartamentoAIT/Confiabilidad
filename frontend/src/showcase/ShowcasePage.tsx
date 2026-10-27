import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { flushSync } from "react-dom";
import { useTranslation } from "react-i18next";

import { Button } from "../components/Button";
import { FormMessage } from "../components/FormMessage";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { CodeField } from "../components/fields/CodeField";
import { PasswordField } from "../components/fields/PasswordField";
import { RequiredLegend } from "../components/fields/RequiredLegend";
import { TextField } from "../components/fields/TextField";
import { newPasswordRules } from "../forms/passwordRules";
import { useFormValidation, type FieldError } from "../forms/useFormValidation";
import type { LanguageStorage } from "../i18n/language";
import { email, required, sixDigitCode } from "./validators";

const FIELDS = {
  name: [required],
  email: [required, email],
  password: [required],
  newPassword: [required, ...newPasswordRules],
  code: [required, sixDigitCode],
};

// La página de muestra no envía nada: simula la espera de una respuesta (RF-022).
const SIMULATED_DELAY_MS = 3000;

type ShowcasePageProps = {
  storage?: LanguageStorage;
};

export function ShowcasePage({ storage }: ShowcasePageProps) {
  const { t } = useTranslation();
  const formTitleId = useId();
  const [processing, setProcessing] = useState(false);
  const { errors, onBlur, handleSubmit } = useFormValidation(FIELDS, { processing });
  const [demoSent, setDemoSent] = useState(false);
  const messageRef = useRef<HTMLDivElement>(null);
  const timer = useRef<number>();

  useEffect(() => () => window.clearTimeout(timer.current), []);

  function simulateSending() {
    setProcessing(true);
    timer.current = window.setTimeout(() => {
      flushSync(() => {
        setProcessing(false);
        setDemoSent(true);
      });
      messageRef.current?.focus();
    }, SIMULATED_DELAY_MS);
  }

  // El mensaje general se retira en cada envío (RF-017).
  function submit(event: FormEvent<HTMLFormElement>) {
    setDemoSent(false);
    handleSubmit(simulateSending)(event);
  }

  const errorText = (error: FieldError | undefined) =>
    error && t(`validation.${error.key}`, error.params);

  return (
    <main>
      <LanguageSwitcher storage={storage} />
      <h1>{t("app.heading")}</h1>
      <p>{t("app.intro")}</p>
      <h2 id={formTitleId}>{t("showcase.formTitle")}</h2>
      <RequiredLegend />
      {demoSent && <FormMessage ref={messageRef} type="info" messageKey="showcase.demoInfo" />}
      <form aria-labelledby={formTitleId} noValidate onSubmit={submit}>
        <TextField
          label={t("showcase.nameLabel")}
          name="name"
          autoComplete="name"
          required
          error={errorText(errors.name)}
          onBlur={onBlur("name")}
        />
        <TextField
          label={t("showcase.emailLabel")}
          name="email"
          type="email"
          required
          error={errorText(errors.email)}
          onBlur={onBlur("email")}
        />
        <PasswordField
          label={t("showcase.passwordLabel")}
          name="password"
          kind="current"
          required
          error={errorText(errors.password)}
          onBlur={onBlur("password")}
        />
        <PasswordField
          label={t("showcase.newPasswordLabel")}
          name="newPassword"
          kind="new"
          required
          error={errorText(errors.newPassword)}
          onBlur={onBlur("newPassword")}
        />
        <CodeField
          label={t("showcase.codeLabel")}
          name="code"
          required
          error={errorText(errors.code)}
          onBlur={onBlur("code")}
        />
        <Button type="submit" keepFocusOnMouseDown processing={processing}>
          {t("showcase.submit")}
        </Button>
      </form>
    </main>
  );
}
