import { useEffect, useState, type MouseEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type { ApiClient } from "../api/client";
import {
  fetchOptions,
  fetchStatus,
  resendCode,
  verifyCode,
  type RegistrationStatus,
} from "../api/registration";
import { Button } from "../components/Button";
import { FormMessage } from "../components/FormMessage";
import { CodeField } from "../components/fields/CodeField";
import {
  useFormValidation,
  type FieldError,
  type GeneralMessage,
  type ValidationKey,
} from "../forms/useFormValidation";
import type { LanguageStorage } from "../i18n/language";
import { PublicLayout } from "../layouts/PublicLayout";
import { PublicPage } from "../layouts/PublicPage";
import { navigate, useLocation } from "../routing/router";
import { required, sixDigitCode } from "../showcase/validators";
import { PasswordStep } from "./PasswordStep";
import { translateCode } from "./serverErrors";
import { useCountdown } from "./useCountdown";
import "./verify.css";

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
  // Cada reenvío vuelve a pedir el estado; cada estado recibido monta de nuevo el formulario del
  // código, para que tome su bloqueo.
  const [generation, setGeneration] = useState(0);
  const [loads, setLoads] = useState(0);
  const [resendMessage, setResendMessage] = useState<GeneralMessage | null>(null);
  // Con un 429 la espera del botón es la del límite, y se anuncia como tal (RF-024).
  const [resendLimited, setResendLimited] = useState(false);
  // El código aceptado solo vive en memoria: recargar vuelve a la verificación (RF-011, S-08).
  const [acceptedCode, setAcceptedCode] = useState<string | null>(null);
  const [rejection, setRejection] = useState<ValidationKey | null>(null);
  const expiry = useCountdown();
  const resendWait = useCountdown();
  const { start } = expiry;
  const { start: startResendWait } = resendWait;

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
        startResendWait(result.data.resend_in);
        setStatus(result.data);
        setLoads((current) => current + 1);
        setLoaded("ready");
      } else if (result.kind === "notFound") setLoaded("notFound");
      else if (result.kind === "networkError") setLoaded("networkError");
      else setLoaded("failed");
    }
    void load();
    return () => {
      current = false;
    };
  }, [client, publicId, start, startResendWait, generation]);

  async function resend() {
    setResendMessage(null);
    setResendLimited(false);
    const result = await resendCode(client, publicId);
    if (result.kind === "ok") {
      setResendMessage({ type: "info", messageKey: "register.resent" });
      setGeneration((current) => current + 1);
    } else if (result.kind === "notFound") setLoaded("notFound");
    else if (result.kind === "rateLimited") {
      setResendLimited(true);
      resendWait.start(result.retryAfter);
    } else {
      setResendMessage({
        type: "error",
        messageKey:
          result.kind === "refused"
            ? "validation.resendUnavailable"
            : result.kind === "networkError"
              ? "validation.networkError"
              : "validation.serverError",
      });
    }
  }

  function codeRejected(code: string) {
    setAcceptedCode(null);
    if (code === "not_found") {
      setLoaded("notFound");
      return;
    }
    setRejection(translateCode(code).key);
    setGeneration((current) => current + 1);
  }

  if (loaded === "notFound") return <InvalidLink storage={storage} />;

  return (
    <PublicLayout storage={storage}>
      <PublicPage title={t("register.verifyTitle")}>
        <p>{t("register.verifyText")}</p>
        {loaded === "networkError" && (
          <FormMessage type="error" messageKey="validation.networkError" />
        )}
        {loaded === "failed" && <FormMessage type="error" messageKey="validation.serverError" />}
        {loaded === "ready" && status && acceptedCode && (
          <PasswordStep
            client={client}
            publicId={publicId}
            code={acceptedCode}
            onCreated={() => navigate("/register/done")}
            onCodeRejected={codeRejected}
          />
        )}
        {loaded === "ready" && status && !acceptedCode && (
          <>
            {rejection && <FormMessage type="error" messageKey={`validation.${rejection}`} />}
            <p>
              {expiry.remaining > 0
                ? t("register.codeExpiresIn", { time: minutesAndSeconds(expiry.remaining) })
                : t("register.codeExpiredNotice")}
            </p>
            <CodeForm
              key={loads}
              client={client}
              publicId={publicId}
              initiallyLocked={status.locked}
              onVerified={setAcceptedCode}
              onNotFound={() => setLoaded("notFound")}
              secondaryAction={
                <Button
                  variant="secondary"
                  disabled={resendWait.remaining > 0 || status.resends_left === 0}
                  onClick={() => void resend()}
                >
                  {resendWait.remaining > 0
                    ? t("register.resendIn", { seconds: resendWait.remaining })
                    : t("register.resend")}
                </Button>
              }
            />
            {status.resends_left > 0 ? (
              <p className="resend-count">
                {t("register.resendsLeft", { count: status.resends_left })}
              </p>
            ) : (
              <>
                <p className="resend-count">{t("register.noResendsLeft")}</p>
                <FormLink />
              </>
            )}
            {/* Hueco reservado de dos líneas para los mensajes del reenvío: aparecen y desaparecen sin
                cambiar el alto de la card (RF-003). */}
            <div className="resend-slot">
              {resendMessage && (
                <FormMessage type={resendMessage.type} messageKey={resendMessage.messageKey} />
              )}
              {resendLimited && resendWait.remaining > 0 && (
                <p role="status">{t("validation.retryIn", { seconds: resendWait.remaining })}</p>
              )}
            </div>
          </>
        )}
      </PublicPage>
    </PublicLayout>
  );
}

type CodeFormProps = {
  client: ApiClient;
  publicId: string;
  initiallyLocked: boolean;
  onVerified: (code: string) => void;
  onNotFound: () => void;
  // Botón que va en la misma fila que «Verificar», antes que él (RF-001).
  secondaryAction: ReactNode;
};

function CodeForm({
  client,
  publicId,
  initiallyLocked,
  onVerified,
  onNotFound,
  secondaryAction,
}: CodeFormProps) {
  const { t } = useTranslation();
  const [processing, setProcessing] = useState(false);
  const [locked, setLocked] = useState(initiallyLocked);
  const wait = useCountdown();
  const { errors, onBlur, handleSubmit, showResult, message, formRef, messageRef } =
    useFormValidation(CODE_FIELDS, { processing });

  // El servidor responde `wrong_code` al intento que agota los cinco y `locked` solo después: el
  // estado dice si este ya bloqueó el código (RF-009, S-10). Consultarlo no cuenta para el límite.
  async function checkLock() {
    const current = await fetchStatus(client, publicId);
    if (current.kind === "ok" && current.data.locked) setLocked(true);
    else if (current.kind === "notFound") onNotFound();
  }

  async function send({ code }: { code: string }) {
    setProcessing(true);
    const result = await verifyCode(client, publicId, code);
    setProcessing(false);
    if (result.kind === "ok") onVerified(code);
    else if (result.kind === "notFound") onNotFound();
    else if (result.kind === "rateLimited") wait.start(result.retryAfter);
    else if (result.kind === "refused" && result.code === "locked") setLocked(true);
    else if (result.kind === "refused" && CODE_ERRORS.has(result.code)) {
      showResult({ fieldErrors: { code: translateCode(result.code) } });
      if (result.code === "wrong_code") await checkLock();
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
        <div className="form-actions">
          {secondaryAction}
          <Button
            type="submit"
            keepFocusOnMouseDown
            processing={processing}
            disabled={locked || wait.remaining > 0}
          >
            {t("register.verifySubmit")}
          </Button>
        </div>
      </form>
    </>
  );
}

function FormLink() {
  const { t } = useTranslation();

  function goToForm(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    navigate("/register");
  }

  return (
    <a href="/register" onClick={goToForm}>
      {t("register.backToForm")}
    </a>
  );
}

function InvalidLink({ storage }: { storage?: LanguageStorage }) {
  const { t } = useTranslation();
  return (
    <PublicLayout storage={storage}>
      <PublicPage title={t("register.invalidLinkTitle")}>
        <p>{t("validation.linkNotFound")}</p>
        <FormLink />
      </PublicPage>
    </PublicLayout>
  );
}
