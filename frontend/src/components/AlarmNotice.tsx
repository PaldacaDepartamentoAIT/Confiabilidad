import type { ComponentPropsWithoutRef, CSSProperties, ReactNode } from "react";

import { AlarmShape, type AlarmKind } from "../icons/shapes";
import "./AlarmNotice.css";

type AlarmNoticeProps = Omit<ComponentPropsWithoutRef<"div">, "title"> & {
  kind: AlarmKind;
  title?: ReactNode;
  action?: ReactNode;
};

const COLORS: Record<AlarmKind, string> = {
  p1: "var(--p1)",
  p2: "var(--p2)",
  warning: "var(--warn)",
  neutral: "var(--text2)",
};

// El texto va en tinta; el color queda en el borde y en la forma (docs/identidad-visual.md).
export function AlarmNotice({
  kind,
  title,
  action,
  className,
  style,
  children,
  ...rest
}: AlarmNoticeProps) {
  return (
    <div
      {...rest}
      className={["aviso", className].filter(Boolean).join(" ")}
      style={{ "--c": COLORS[kind], ...style } as CSSProperties}
      data-ui="alarm-notice"
    >
      <AlarmShape kind={kind} />
      <div className="tx">
        {title !== undefined && title !== null && <b>{title}</b>} {children}
      </div>
      {action}
    </div>
  );
}
