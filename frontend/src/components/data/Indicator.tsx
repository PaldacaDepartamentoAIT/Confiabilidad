import type { ReactNode } from "react";

import "../Block.css";
import "./Indicator.css";

type IndicatorProps = {
  label: ReactNode;
  value: ReactNode;
  help?: ReactNode;
  variant?: "default" | "featured" | "alert";
};

export function Indicator({ label, value, help, variant = "default" }: IndicatorProps) {
  return (
    <div
      className={["block", "kpi", variant !== "default" && variant].filter(Boolean).join(" ")}
      data-ui="indicator"
    >
      <div className="lab">{label}</div>
      <div className="num">{value}</div>
      {help !== undefined && <div className="help">{help}</div>}
    </div>
  );
}

export function IndicatorGrid({ children }: { children: ReactNode }) {
  return <div className="kpis">{children}</div>;
}
