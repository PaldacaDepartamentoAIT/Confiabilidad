import { useEffect, useId, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import type { ApiClient } from "../api/client";
import { fetchOptions, type RegistrationOptions } from "../api/registration";
import { Button } from "../components/Button";
import { FormMessage } from "../components/FormMessage";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { Checkbox } from "../components/fields/Checkbox";
import { RequiredLegend } from "../components/fields/RequiredLegend";
import { SelectField } from "../components/fields/SelectField";
import { TextField } from "../components/fields/TextField";
import { useFormValidation, type FieldError, type Validator } from "../forms/useFormValidation";
import type { LanguageStorage } from "../i18n/language";
import { email, required } from "../showcase/validators";

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
};

type Loaded =
  { status: "loading" } | { status: "failed" } | { status: "ready"; options: RegistrationOptions };

type RegisterPageProps = {
  client: ApiClient;
  storage?: LanguageStorage;
};

export function RegisterPage({ client, storage }: RegisterPageProps) {
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
      <LanguageSwitcher storage={storage} />
      <h1 id={titleId}>{t("register.title")}</h1>
      {loaded.status === "failed" && (
        <FormMessage type="error" messageKey="validation.networkError" />
      )}
      {loaded.status === "ready" &&
        (loaded.options.terms ? (
          <RegisterForm options={loaded.options} language={i18n.language} titleId={titleId} />
        ) : (
          <FormMessage type="error" messageKey="validation.termsUnavailable" />
        ))}
    </main>
  );
}

type RegisterFormProps = {
  options: RegistrationOptions;
  language: string;
  titleId: string;
};

function RegisterForm({ options, language, titleId }: RegisterFormProps) {
  const { t } = useTranslation();
  const { errors, onBlur, handleSubmit, message, formRef, messageRef } = useFormValidation(FIELDS, {
    scrollToError: true,
  });

  const countries = useMemo(() => {
    const names = new Intl.DisplayNames([language], { type: "region" });
    return options.countries
      .map((code) => ({ value: code, label: names.of(code) ?? code }))
      .sort((first, second) => first.label.localeCompare(second.label, language));
  }, [options.countries, language]);

  const errorText = (error: FieldError | undefined) =>
    error && t(`validation.${error.key}`, error.params);

  return (
    <>
      <RequiredLegend />
      {message && (
        <FormMessage ref={messageRef} type={message.type} messageKey={message.messageKey} />
      )}
      <form
        ref={formRef}
        aria-labelledby={titleId}
        noValidate
        onSubmit={handleSubmit(() => undefined)}
      >
        <TextField
          label={t("register.nameLabel")}
          name="name"
          autoComplete="name"
          required
          error={errorText(errors.name)}
          onBlur={onBlur("name")}
        />
        <TextField
          label={t("register.birthdateLabel")}
          name="birthdate"
          type="date"
          autoComplete="bday"
          required
          error={errorText(errors.birthdate)}
          onBlur={onBlur("birthdate")}
        />
        <TextField
          label={t("register.emailLabel")}
          name="email"
          type="email"
          required
          error={errorText(errors.email)}
          onBlur={onBlur("email")}
        />
        <SelectField
          label={t("register.countryLabel")}
          placeholder={t("register.countryPlaceholder")}
          name="country"
          options={countries}
          autoComplete="country"
          required
          error={errorText(errors.country)}
          onBlur={onBlur("country")}
        />
        <details>
          <summary>{t("register.termsTitle")}</summary>
          <p>{options.terms?.content}</p>
        </details>
        <Checkbox
          label={t("register.termsLabel")}
          name="terms"
          required
          error={errorText(errors.terms)}
          onBlur={onBlur("terms")}
        />
        {options.marketing && (
          <>
            <details>
              <summary>{t("register.marketingTitle")}</summary>
              <p>{options.marketing.content}</p>
            </details>
            <Checkbox label={t("register.marketingLabel")} name="marketing" />
          </>
        )}
        <Button type="submit" keepFocusOnMouseDown>
          {t("register.submit")}
        </Button>
      </form>
    </>
  );
}
