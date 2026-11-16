import type { ComponentPropsWithoutRef } from "react";

import "./Chip.css";

export function Chip({ className, children, ...rest }: ComponentPropsWithoutRef<"span">) {
  return (
    <span {...rest} className={["chip", className].filter(Boolean).join(" ")} data-ui="chip">
      {children}
    </span>
  );
}
