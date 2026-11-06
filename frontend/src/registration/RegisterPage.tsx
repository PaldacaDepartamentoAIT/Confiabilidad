import { useEffect, useId, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";

import type { ApiClient } from "../api/client";
import {
  fetchOptions,
  submitRegistration,
  type LegalDocument,
  type RegistrationOptions,
} from "../api/registration";
import { Button } from "../components/Button";
import { FormMessage } from "../components/FormMessage";
import { MessageZone } from "../components/MessageZone";
import { Checkbox } from "../components/fields/Checkbox";
import { RequiredLegend } from "../components/fields/RequiredLegend";
import { SelectField } from "../components/fields/SelectField";
import { TextField } from "../components/fields/TextField";
import {
  useFormValidation,
  type FieldError,
  type SubmitResult,
  type Validator,
} from "../forms/useFormValidation";
import { navigate } from "../routing/router";
import { email, required } from "../showcase/validators";
import { translateFieldErrors } from "./serverErrors";
import { useCountdown } from "./useCountdown";

const chosen =
  (key: FieldError["key"]): Validator =>
  (value) =>
    value ? null : { key };

// Solo las comprobaciones de RF-002; edad, país y formato estricto del correo los decide el servidor.
const FIELDS = {
  name: [required],
  birthdate: [required],
  email: [required, email],
  country: [chosen("countryInvalid")],
  terms: [chosen("termsNotAccepted")],
  marketing: [],
};

type Field = keyof typeof FIELDS;

const FAILURE = { type: "error", messageKey: "validation.serverError" } as const;
const NETWORK = { type: "error", messageKey: "validation.networkError" } as const;
const UNKNOWN = { type: "error", messageKey: "validation.unknownError" } as const;

// Un error de un campo que la pantalla no tiene no se puede pintar bajo él: va como mensaje general.
function fieldResult(errors: Record<string, string[]>): SubmitResult<Field> {
  const known = Object.keys(errors).every((name) => name in FIELDS);
  return { fieldErrors: translateFieldErrors(errors), message: known ? undefined : UNKNOWN };
}

type Loaded =
  { status: "loading" } | { status: "failed" } | { status: "ready"; options: RegistrationOptions };

type RegisterPageProps = {
  client: ApiClient;
};

export function RegisterPage({ client }: RegisterPageProps) {
  const { t, i18n } = useTranslation();
  const titleId = useId();
  const [loaded, setLoaded] = useState<Loaded>({ status: "loading" });

  useEffect(() => {
    let current = true;
    void fetchOptions(client).then((result) => {
      if (!current) return;
      setLoaded(
        result.kind === "ok" ? { status: "ready", options: result.data } : { status: "failed" },
      );
    });
    return () => {
      current = false;
    };
  }, [client]);

  return (
    <main>
      <h1 id={titleId}>{t("register.title")}</h1>
      {loaded.status === "failed" && (
        <FormMessage type="error" messageKey="validation.networkError" />
      )}
      {loaded.status === "ready" &&
        (loaded.options.terms ? (
          <RegisterForm
            client={client}
            options={loaded.options}
            terms={loaded.options.terms}
            language={i18n.language}
            titleId={titleId}
          />
        ) : (
          <FormMessage type="error" messageKey="validation.termsUnavailable" />
        ))}
    </main>
  );
}

type RegisterFormProps = {
  client: ApiClient;
  options: RegistrationOptions;
  terms: LegalDocument;
  language: string;
  titleId: string;
};

function RegisterForm({ client, options, terms, language, titleId }: RegisterFormProps) {
  const { t } = useTranslation();
  const [processing, setProcessing] = useState(false);
  const wait = useCountdown();
  const { allErrors, onBlur, handleSubmit, showResult, message, formRef, messageRef } =
    useFormValidation(FIELDS, { scrollToError: true, processing });

  async function send(values: Record<Field, string>) {
    const { marketing } = options;
    setProcessing(true);
    const result = await submitRegistration(client, {
      name: values.name,
      birthdate: values.birthdate,
      email: values.email,
      country: values.country,
      terms: { version: terms.version, locale: terms.locale },
      ...(values.marketing && marketing
        ? { marketing: { version: marketing.version, locale: marketing.locale } }
        : {}),
    });
    setProcessing(false);
    if (result.kind === "ok") navigate(`/register/continue#${result.data.public_id}`);
    else if (result.kind === "fieldErrors") showResult(fieldResult(result.errors));
    else if (result.kind === "rateLimited") wait.start(result.retryAfter);
    else if (result.kind === "networkError") showResult({ message: NETWORK });
    else if (result.kind === "refused") showResult({ message: UNKNOWN });
    else showResult({ message: FAILURE });
  }

  const countries = useMemo(() => {
    const names = new Intl.DisplayNames([language], { type: "region" });
    return options.countries
      .map((code) => ({ value: code, label: names.of(code) ?? code }))
      .sort((first, second) => first.label.localeCompare(second.label, language));
  }, [options.countries, language]);

  const errorText = (list: readonly FieldError[] | undefined) =>
    list?.map((error) => t(`validation.${error.key}`, error.params)).join(" ") || undefined;

  return (
    <>
      <RequiredLegend />
      <form
        ref={formRef}
        aria-labelledby={titleId}
        noValidate
        onSubmit={handleSubmit((values) => void send(values))}
      >
        <TextField
          label={t("register.nameLabel")}
          help={t("help.name")}
          name="name"
          autoComplete="name"
          required
          error={errorText(allErrors.name)}
          onBlur={onBlur("name")}
        />
        <TextField
          label={t("register.birthdateLabel")}
          help={t("help.birthdate")}
          name="birthdate"
          type="date"
          autoComplete="bday"
          required
          error={errorText(allErrors.birthdate)}
          onBlur={onBlur("birthdate")}
        />
        <TextField
          label={t("register.emailLabel")}
          help={t("help.email")}
          name="email"
          type="email"
          required
          error={errorText(allErrors.email)}
          onBlur={onBlur("email")}
        />
        <SelectField
          label={t("register.countryLabel")}
          help={t("help.country")}
          placeholder={t("register.countryPlaceholder")}
          name="country"
          options={countries}
          required
          error={errorText(allErrors.country)}
          onBlur={onBlur("country")}
        />
        <details>
          <summary>{t("register.termsTitle")}</summary>
          <Markdown>{terms.content}</Markdown>
        </details>
        <Checkbox
          label={t("register.termsLabel")}
          name="terms"
          required
          error={errorText(allErrors.terms)}
          onBlur={onBlur("terms")}
        />
        {options.marketing && (
          <>
            <details>
              <summary>{t("register.marketingTitle")}</summary>
              <Markdown>{options.marketing.content}</Markdown>
            </details>
            <Checkbox label={t("register.marketingLabel")} name="marketing" />
          </>
        )}
        <MessageZone>
          {wait.remaining > 0 && (
            <p role="status">{t("validation.retryIn", { seconds: wait.remaining })}</p>
          )}
          {message && (
            <FormMessage ref={messageRef} type={message.type} messageKey={message.messageKey} />
          )}
        </MessageZone>
        <Button
          type="submit"
          keepFocusOnMouseDown
          processing={processing}
          disabled={wait.remaining > 0}
        >
          {t("register.submit")}
        </Button>
      </form>
    </>
  );
}
