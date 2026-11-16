import type { ComponentPropsWithoutRef } from "react";

import { IconCheck, IconInfo } from "../icons";
import "./Notice.css";

type NoticeProps = ComponentPropsWithoutRef<"div"> & {
  kind?: "info" | "success";
};

// Aviso sin color propio: borde izquierdo de 4 px en texto secundario (docs/identidad-visual.md).
export function Notice({
  kind = "info",
  role = "status",
  className,
  children,
  ...rest
}: NoticeProps) {
  const Icon = kind === "success" ? IconCheck : IconInfo;
  return (
    <div
      {...rest}
      role={role}
      className={["notice", className].filter(Boolean).join(" ")}
      data-ui="notice"
    >
      <Icon />
      <span>{children}</span>
    </div>
  );
}
