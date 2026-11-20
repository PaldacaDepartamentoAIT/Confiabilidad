import {
  useEffect,
  useRef,
  useState,
  type MouseEvent as ReactMouseEvent,
  type ReactNode,
} from "react";

import { AlarmShape, type AlarmKind } from "../../icons/shapes";
import "./Table.css";

export type StatusCell = { text: ReactNode; kind?: AlarmKind };

export type TableColumn = {
  key: string;
  header: ReactNode;
  // «text» por defecto; «code» usa la fuente monoespaciada; «status» espera un `StatusCell`.
  kind?: "text" | "code" | "status";
};

export type TableRow = { id: string; cells: Record<string, ReactNode | StatusCell> };

type TableProps = {
  label: string;
  columns: TableColumn[];
  rows: TableRow[];
  emptyMessage: ReactNode;
};

const MIN_COLUMN_WIDTH = 48;
const DEFAULT_COLUMN_WIDTH = 120;

function Status({ text, kind }: StatusCell) {
  return (
    <span className="st">
      {kind ? <AlarmShape kind={kind} /> : <span className="shape" aria-hidden="true" />}
      <span className="st-text">{text}</span>
    </span>
  );
}

export function Table({ label, columns, rows, emptyMessage }: TableProps) {
  const headerRefs = useRef<Record<string, HTMLTableCellElement | null>>({});
  const dragCleanup = useRef<(() => void) | null>(null);
  const [widths, setWidths] = useState<Record<string, number> | null>(null);
  const [resizingKey, setResizingKey] = useState<string | null>(null);

  useEffect(() => () => dragCleanup.current?.(), []);

  const activeWidths =
    widths && columns.every((column) => typeof widths[column.key] === "number") ? widths : null;
  const fixedSum = activeWidths
    ? columns.slice(0, -1).reduce((sum, column) => sum + activeWidths[column.key], 0)
    : 0;
  const minTableWidth = activeWidths ? Math.max(640, fixedSum + MIN_COLUMN_WIDTH) : undefined;

  function startResize(key: string, event: ReactMouseEvent<HTMLSpanElement>) {
    event.preventDefault();
    dragCleanup.current?.();

    const snapshot: Record<string, number> = {};
    for (const column of columns) {
      const measured = headerRefs.current[column.key]?.getBoundingClientRect().width ?? 0;
      snapshot[column.key] =
        activeWidths?.[column.key] ?? (measured > 0 ? measured : DEFAULT_COLUMN_WIDTH);
    }

    const startX = event.clientX;
    const startWidth = snapshot[key];
    setWidths(snapshot);
    setResizingKey(key);

    function onMouseMove(moveEvent: MouseEvent) {
      const nextWidth = Math.max(
        MIN_COLUMN_WIDTH,
        Math.round(startWidth + (moveEvent.clientX - startX)),
      );
      setWidths((current) => ({ ...(current ?? snapshot), [key]: nextWidth }));
    }

    function cleanup() {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", cleanup);
      dragCleanup.current = null;
      setResizingKey(null);
    }

    dragCleanup.current = cleanup;
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", cleanup);
  }

  return (
    <div className="table-wrap" role="region" aria-label={label} tabIndex={0}>
      <table
        data-ui="table"
        className={activeWidths ? "data-table resized" : "data-table"}
        style={minTableWidth !== undefined ? { minWidth: `${minTableWidth}px` } : undefined}
      >
        {activeWidths && (
          <colgroup>
            {columns.map((column, index) => (
              <col
                key={column.key}
                style={
                  index < columns.length - 1
                    ? { width: `${activeWidths[column.key]}px` }
                    : undefined
                }
              />
            ))}
          </colgroup>
        )}
        <thead>
          <tr>
            {columns.map((column, index) => (
              <th
                key={column.key}
                ref={(node) => {
                  headerRefs.current[column.key] = node;
                }}
                scope="col"
                className={resizingKey === column.key ? "resizing" : undefined}
              >
                <span className="th-label">{column.header}</span>
                {index < columns.length - 1 && (
                  <span
                    className="col-resize"
                    aria-hidden="true"
                    onMouseDown={(event) => startResize(column.key, event)}
                  />
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td className="empty" colSpan={columns.length}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                {columns.map((column) => {
                  const cell = row.cells[column.key];
                  return (
                    <td key={column.key} className={column.kind === "code" ? "mono" : undefined}>
                      {column.kind === "status" ? (
                        <Status {...(cell as StatusCell)} />
                      ) : (
                        (cell as ReactNode)
                      )}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
