import { useEffect, useRef, type ButtonHTMLAttributes } from "react";
import { useTranslation } from "react-i18next";

import { useAnnouncer } from "./announcer";
import "./Button.css";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  type?: "button" | "submit";
  keepFocusOnMouseDown?: boolean;
  processing?: boolean;
  variant?: "primary" | "secondary";
};

export function Button({
  type = "button",
  keepFocusOnMouseDown = false,
  processing = false,
  variant = "primary",
  className,
  onMouseDown,
  onClick,
  children,
  ...buttonProps
}: ButtonProps) {
  const { t } = useTranslation();
  const announce = useAnnouncer();
  const wasProcessing = useRef(processing);

  useEffect(() => {
    if (processing && !wasProcessing.current) {
      announce(t("button.processingAnnouncement"), "polite");
    }
    wasProcessing.current = processing;
  }, [processing, announce, t]);

  return (
    <button
      {...buttonProps}
      type={type}
      className={["btn", variant === "primary" ? "btn-primary" : "btn-ghost hov", className]
        .filter(Boolean)
        .join(" ")}
      data-ui={`button-${variant}`}
      // `aria-disabled` en lugar de `disabled`: el botón sigue en el orden de Tab y no pierde el foco (D-07).
      aria-disabled={processing || undefined}
      onMouseDown={(event) => {
        // Sin quitar el foco al campo, su error no desaparece bajo el puntero y el clic llega (D-17).
        if (keepFocusOnMouseDown) event.preventDefault();
        onMouseDown?.(event);
      }}
      onClick={(event) => {
        if (processing) {
          event.preventDefault();
          return;
        }
        onClick?.(event);
      }}
    >
      {processing ? t("button.processing") : children}
    </button>
  );
}
