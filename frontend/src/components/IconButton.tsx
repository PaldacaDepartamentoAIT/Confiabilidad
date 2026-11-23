import { useEffect, useRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { useAnnouncer } from "./announcer";
import "../theme/ThemeButton.css";
import "./IconButton.css";

type IconButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "aria-label" | "children"> & {
  label: string;
  icon: ReactNode;
  type?: "button" | "submit";
  size?: "md" | "sm";
  keepFocusOnMouseDown?: boolean;
  processing?: boolean;
  tooltipAlign?: "center" | "end";
};

export function IconButton({
  label,
  icon,
  type = "button",
  size = "md",
  keepFocusOnMouseDown = false,
  processing = false,
  tooltipAlign = "center",
  className,
  onMouseDown,
  onClick,
  ...buttonProps
}: IconButtonProps) {
  const { t } = useTranslation();
  const announce = useAnnouncer();
  const wasProcessing = useRef(processing);

  useEffect(() => {
    if (processing && !wasProcessing.current) {
      announce(t("button.processingAnnouncement"), "polite");
    }
    wasProcessing.current = processing;
  }, [processing, announce, t]);

  const accessibleLabel = processing ? t("button.processing") : label;

  return (
    <span className="icon-btn-wrap">
      <button
        {...buttonProps}
        type={type}
        className={["icon-btn hov", size === "sm" && "icon-btn-sm", className]
          .filter(Boolean)
          .join(" ")}
        data-ui="icon-button"
        aria-label={accessibleLabel}
        aria-disabled={processing || undefined}
        onMouseDown={(event) => {
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
        {icon}
      </button>
      <span
        className={["icon-btn-tip", tooltipAlign === "end" && "icon-btn-tip-end"]
          .filter(Boolean)
          .join(" ")}
        aria-hidden="true"
      >
        {accessibleLabel}
      </span>
    </span>
  );
}
