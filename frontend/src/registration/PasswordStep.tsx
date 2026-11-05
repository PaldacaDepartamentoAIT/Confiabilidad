import { useId, useState } from "react";
import { useTranslation } from "react-i18next";

import type { ApiClient } from "../api/client";
import { completeRegistration } from "../api/registration";
import { Button } from "../components/Button";
import { FormMessage } from "../components/FormMessage";
import { MessageZone } from "../components/MessageZone";
import { PasswordField } from "../components/fields/PasswordField";
import { newPasswordRules } from "../forms/passwordRules";
import { useFormValidation, type FieldError } from "../forms/useFormValidation";
import { required } from "../showcase/validators";
import { translateFieldErrors } from "./serverErrors";
import { useCountdown } from "./useCountdown";

const FIELDS = { password: [required, ...newPasswordRules] };

type PasswordStepProps = {
  client: ApiClient;
  publicId: string;
  code: string;
  onCreated: () => void;
  // Un rechazo del código lo resuelve quien guarda el código (RF-011); aquí no se reintenta.
  onCodeRejected: (code: string) => void;
};

export function PasswordStep({
  client,
  publicId,
  code,
  onCreated,
  onCodeRejected,
}: PasswordStepProps) {
  const { t } = useTranslation();
  const titleId = useId();
  const [processing, setProcessing] = useState(false);
  const wait = useCountdown();
  const { allErrors, onBlur, handleSubmit, showResult, message, formRef, messageRef } =
    useFormValidation(FIELDS, { processing });

  async function send({ password }: { password: string }) {
    setProcessing(true);
    const result = await completeRegistration(client, publicId, code, password);
    setProcessing(false);
    if (result.kind === "ok") onCreated();
    else if (result.kind === "fieldErrors")
      showResult({ fieldErrors: translateFieldErrors(result.errors) });
    else if (result.kind === "refused") onCodeRejected(result.code);
    else if (result.kind === "notFound") onCodeRejected("not_found");
    else if (result.kind === "rateLimited") wait.start(result.retryAfter);
    else {
      const key =
        result.kind === "networkError" ? "validation.networkError" : "validation.serverError";
      showResult({ message: { type: "error", messageKey: key } });
    }
  }

  const errorText = (list: readonly FieldError[] | undefined) =>
    list?.map((error) => t(`validation.${error.key}`, error.params)).join(" ") || undefined;

  return (
    <section aria-labelledby={titleId}>
      <h2 id={titleId}>{t("register.passwordTitle")}</h2>
      <form ref={formRef} noValidate onSubmit={handleSubmit((values) => void send(values))}>
        <PasswordField
          label={t("register.passwordLabel")}
          help={t("help.password")}
          name="password"
          kind="new"
          required
          error={errorText(allErrors.password)}
          onBlur={onBlur("password")}
        />
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
          {t("register.passwordSubmit")}
        </Button>
      </form>
    </section>
  );
}
