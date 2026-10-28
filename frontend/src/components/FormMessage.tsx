import type { ParseKeys } from "i18next";
import { forwardRef } from "react";
import { useTranslation } from "react-i18next";

export type MessageType = "error" | "success" | "info";

type FormMessageProps = {
  type: MessageType;
  messageKey: ParseKeys;
};

// El prefijo visible dice al lector el tipo de mensaje cuando recibe el foco (D-11).
export const FormMessage = forwardRef<HTMLDivElement, FormMessageProps>(function FormMessage(
  { type, messageKey },
  ref,
) {
  const { t } = useTranslation();
  return (
    <div ref={ref} tabIndex={-1}>
      <strong>{t(`message.${type}`)}</strong> {t(messageKey)}
    </div>
  );
});
