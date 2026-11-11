import type { ReactNode } from "react";

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

function Status({ text, kind }: StatusCell) {
  return (
    <span className="st">
      {kind ? <AlarmShape kind={kind} /> : <span className="shape" aria-hidden="true" />}
      {text}
    </span>
  );
}

export function Table({ label, columns, rows, emptyMessage }: TableProps) {
  return (
    <div className="table-wrap" role="region" aria-label={label} tabIndex={0}>
      <table data-ui="table" className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col">
                {column.header}
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
