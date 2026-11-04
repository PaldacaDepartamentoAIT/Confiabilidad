import { useEffect, useState, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";

import type { ApiClient } from "../api/client";
import {
  fetchOptions,
  fetchStatus,
  verifyCode,
  type RegistrationStatus,
} from "../api/registration";
import { Button } from "../components/Button";
import { FormMessage } from "../components/FormMessage";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { CodeField } from "../components/fields/CodeField";
import { useFormValidation, type FieldError } from "../forms/useFormValidation";
import type { LanguageStorage } from "../i18n/language";
import { navigate, useLocation } from "../routing/router";
import { required, sixDigitCode } from "../showcase/validators";
import { translateCode } from "./serverErrors";
import { useCountdown } from "./useCountdown";

const CODE_FIELDS = { code: [required, sixDigitCode] };

// Estos rechazos se refieren al código escrito y se pintan bajo el campo (RF-007).
const CODE_ERRORS = new Set(["wrong_code", "code_expired"]);

type Loaded = "loading" | "ready" | "notFound" | "networkError" | "failed";

function hasCsrfCookie(): boolean {
  return document.cookie.split(";").some((part) => part.trim().startsWith("csrftoken="));
}

function minutesAndSeconds(total: number): string {
  const seconds = String(total % 60).padStart(2, "0");
  return `${Math.floor(total / 60)}:${seconds}`;
}

type VerifyPageProps = {
  client: ApiClient;
  storage?: LanguageStorage;
};

export function VerifyPage({ client, storage }: VerifyPageProps) {
  const { t } = useTranslation();
  const publicId = useLocation().hash;
  const [loaded, setLoaded] = useState<Loaded>(publicId ? "loading" : "notFound");
  const [status, setStatus] = useState<RegistrationStatus | null>(null);
  const expiry = useCountdown();
  const { start } = expiry;

  useEffect(() => {
    if (!publicId) return;
    let current = true;
    async function load() {
      // El enlace del correo puede abrirse en un navegador sin la cookie CSRF que piden los POST (D-09).
      if (!hasCsrfCookie()) await fetchOptions(client);
      const result = await fetchStatus(client, publicId);
      if (!current) return;
      if (result.kind === "ok") {
        start(result.data.code_expires_in);
        setStatus(result.data);
        setLoaded("ready");
      } else if (result.kind === "notFound") setLoaded("notFound");
      else if (result.kind === "networkError") setLoaded("networkError");
      else setLoaded("failed");
    }
    void load();
    return () => {
      current = false;
    };
  }, [client, publicId, start]);

  if (loaded === "notFound") return <InvalidLink storage={storage} />;

  return (
    <main>
      <LanguageSwitcher storage={storage} />
      <h1>{t("register.verifyTitle")}</h1>
      <p>{t("register.verifyText")}</p>
      {loaded === "networkError" && (
        <FormMessage type="error" messageKey="validation.networkError" />
      )}
      {loaded === "failed" && <FormMessage type="error" messageKey="validation.serverError" />}
      {loaded === "ready" && status && (
        <>
          <p>
            {expiry.remaining > 0
              ? t("register.codeExpiresIn", { time: minutesAndSeconds(expiry.remaining) })
              : t("register.codeExpiredNotice")}
          </p>
          <CodeForm
            client={client}
            publicId={publicId}
            initiallyLocked={status.locked}
            onNotFound={() => setLoaded("notFound")}
          />
        </>
      )}
    </main>
  );
}

type CodeFormProps = {
  client: ApiClient;
  publicId: string;
  initiallyLocked: boolean;
  onNotFound: () => void;
};

function CodeForm({ client, publicId, initiallyLocked, onNotFound }: CodeFormProps) {
  const { t } = useTranslation();
  const [processing, setProcessing] = useState(false);
  const [locked, setLocked] = useState(initiallyLocked);
  const wait = useCountdown();
  const { errors, onBlur, handleSubmit, showResult, message, formRef, messageRef } =
    useFormValidation(CODE_FIELDS, { processing });

  async function send({ code }: { code: string }) {
    setProcessing(true);
    const result = await verifyCode(client, publicId, code);
    setProcessing(false);
    if (result.kind === "ok") return;
    if (result.kind === "notFound") onNotFound();
    else if (result.kind === "rateLimited") wait.start(result.retryAfter);
    else if (result.kind === "refused" && result.code === "locked") setLocked(true);
    else if (result.kind === "refused" && CODE_ERRORS.has(result.code)) {
      showResult({ fieldErrors: { code: translateCode(result.code) } });
    } else if (result.kind === "refused") {
      showResult({
        message: { type: "error", messageKey: `validation.${translateCode(result.code).key}` },
      });
    } else if (result.kind === "networkError") {
      showResult({ message: { type: "error", messageKey: "validation.networkError" } });
    } else showResult({ message: { type: "error", messageKey: "validation.serverError" } });
  }

  const errorText = (error: FieldError | undefined) =>
    error && t(`validation.${error.key}`, error.params);

  return (
    <>
      {locked && <p>{t("register.lockedNotice")}</p>}
      {wait.remaining > 0 && (
        <p role="status">{t("validation.retryIn", { seconds: wait.remaining })}</p>
      )}
      {message && (
        <FormMessage ref={messageRef} type={message.type} messageKey={message.messageKey} />
      )}
      <form ref={formRef} noValidate onSubmit={handleSubmit((values) => void send(values))}>
        <CodeField
          label={t("register.codeLabel")}
          name="code"
          required
          error={errorText(errors.code)}
          onBlur={onBlur("code")}
        />
        <Button
          type="submit"
          keepFocusOnMouseDown
          processing={processing}
          disabled={locked || wait.remaining > 0}
        >
          {t("register.verifySubmit")}
        </Button>
      </form>
    </>
  );
}

function InvalidLink({ storage }: { storage?: LanguageStorage }) {
  const { t } = useTranslation();

  function goToForm(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    navigate("/register");
  }

  return (
    <main>
      <LanguageSwitcher storage={storage} />
      <h1>{t("register.invalidLinkTitle")}</h1>
      <p>{t("validation.linkNotFound")}</p>
      <a href="/register" onClick={goToForm}>
        {t("register.backToForm")}
      </a>
    </main>
  );
}
