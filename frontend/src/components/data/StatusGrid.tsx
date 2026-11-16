import { AlarmShape, type AlarmKind } from "../../icons/shapes";
import "./StatusGrid.css";

export type StatusGridCell = { name: string; kind?: AlarmKind };

export type StatusGridLabels = Record<AlarmKind | "normal", string>;

type StatusGridProps = {
  label: string;
  cells: readonly StatusGridCell[];
  labels: StatusGridLabels;
};

// Orden de la leyenda de la referencia: el neutro primero y después las prioridades.
const LEGEND: AlarmKind[] = ["neutral", "p1", "p2", "warning"];

// Rejilla de cuadros de estado: cada cuadro lleva el glifo de su forma además del color, para que el
// estado no dependa solo del color.
export function StatusGrid({ label, cells, labels }: StatusGridProps) {
  return (
    <>
      <div className="cells" role="group" aria-label={label}>
        {cells.map(({ name, kind }) => {
          const text = `${name} · ${labels[kind ?? "normal"]}`;
          return (
            <div
              key={name}
              className={["cell", kind].filter(Boolean).join(" ")}
              role="img"
              title={text}
              aria-label={text}
            >
              {kind && kind !== "neutral" && (
                <AlarmShape kind={kind} size={12} style={{ color: "var(--bg)" }} />
              )}
            </div>
          );
        })}
      </div>
      <div className="legend cells-legend">
        {LEGEND.map((kind) => (
          <span key={kind}>
            <AlarmShape kind={kind} />
            {labels[kind]}
          </span>
        ))}
      </div>
    </>
  );
}
