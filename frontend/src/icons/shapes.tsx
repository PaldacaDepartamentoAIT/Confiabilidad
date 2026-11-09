import type { CSSProperties } from "react";

export type AlarmKind = "p1" | "p2" | "warning" | "neutral";

type AlarmShapeProps = {
  kind: AlarmKind;
  label?: string;
  size?: number;
  className?: string;
  style?: CSSProperties;
};

// Una forma y un color por prioridad (docs/identidad-visual.md, «Estados de alarma»).
const COLORS: Record<AlarmKind, string> = {
  p1: "var(--p1)",
  p2: "var(--p2)",
  warning: "var(--warn)",
  neutral: "var(--text2)",
};

function Drawing({ kind }: { kind: AlarmKind }) {
  switch (kind) {
    case "p1":
      return <rect x="2" y="2" width="12" height="12" fill="currentColor" />;
    case "p2":
      return <path d="M8 2 15 14H1z" fill="currentColor" />;
    case "warning":
      return <path d="M8 1 15 8 8 15 1 8z" fill="currentColor" />;
    case "neutral":
      return (
        <rect
          x="2.5"
          y="2.5"
          width="11"
          height="11"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        />
      );
  }
}

const NAMES: Record<AlarmKind, string> = {
  p1: "square",
  p2: "triangle",
  warning: "diamond",
  neutral: "hollow-square",
};

export function AlarmShape({ kind, label, size = 16, className, style }: AlarmShapeProps) {
  return (
    <svg
      className={["shape", className].filter(Boolean).join(" ")}
      data-shape={NAMES[kind]}
      viewBox="0 0 16 16"
      width={size}
      height={size}
      style={{ color: COLORS[kind], ...style }}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
    >
      <Drawing kind={kind} />
    </svg>
  );
}
