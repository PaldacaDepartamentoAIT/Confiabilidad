import {
  useEffect,
  useRef,
  useState,
  type MouseEvent as ReactMouseEvent,
  type ReactNode,
} from "react";

import { IconCheck } from "../../icons";
import { AlarmShape, type AlarmKind } from "../../icons/shapes";
import "../fields/Checkbox.css";
import "./Table.css";

export type StatusCell = { text: ReactNode; kind?: AlarmKind };

export type TableColumn = {
  key: string;
  header: ReactNode;
  // «text» por defecto; «code» usa la fuente monoespaciada; «status» espera un `StatusCell`.
  kind?: "text" | "code" | "status";
};

export type TableRow = { id: string; cells: Record<string, ReactNode | StatusCell> };

// Selección de filas con casillas: `selectAllLabel` añade la casilla en la cabecera para marcar o
// desmarcar todas las seleccionables; al haber filas marcadas se muestra una barra inferior.
export type TableSelection = {
  selectedIds: ReadonlySet<string>;
  onChange: (next: Set<string>) => void;
  isSelectable?: (row: TableRow) => boolean;
  selectAllLabel?: string;
  rowLabel: (row: TableRow) => string;
  selectedLabel: (count: number) => string;
  actions?: ReactNode;
};

type TableProps = {
  label: string;
  columns: TableColumn[];
  rows: TableRow[];
  emptyMessage: ReactNode;
  selection?: TableSelection;
};

const MIN_COLUMN_WIDTH = 48;
const DEFAULT_COLUMN_WIDTH = 120;
const SELECT_COLUMN_WIDTH = 44;

function Status({ text, kind }: StatusCell) {
  return (
    <span className="st">
      {kind ? <AlarmShape kind={kind} /> : <span className="shape" aria-hidden="true" />}
      <span className="st-text">{text}</span>
    </span>
  );
}

type RowCheckProps = {
  label: string;
  checked: boolean;
  indeterminate?: boolean;
  disabled?: boolean;
  onChange: () => void;
};

function RowCheck({ label, checked, indeterminate = false, disabled, onChange }: RowCheckProps) {
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (input.current) input.current.indeterminate = indeterminate;
  }, [indeterminate]);

  return (
    <label className="check tbl-check">
      <span className="cb">
        <input
          ref={input}
          type="checkbox"
          aria-label={label}
          checked={checked}
          disabled={disabled}
          onChange={onChange}
        />
        <IconCheck size={14} strokeWidth={3} />
      </span>
    </label>
  );
}

export function Table({ label, columns, rows, emptyMessage, selection }: TableProps) {
  const headerRefs = useRef<Record<string, HTMLTableCellElement | null>>({});
  const dragCleanup = useRef<(() => void) | null>(null);
  const [widths, setWidths] = useState<Record<string, number> | null>(null);
  const [resizingKey, setResizingKey] = useState<string | null>(null);

  useEffect(() => () => dragCleanup.current?.(), []);

  const selectableIds = selection
    ? rows.filter((row) => selection.isSelectable?.(row) ?? true).map((row) => row.id)
    : [];
  const selectedCount = selection
    ? selectableIds.filter((id) => selection.selectedIds.has(id)).length
    : 0;
  const allSelected = selectableIds.length > 0 && selectedCount === selectableIds.length;
  const selectWidth = selection ? SELECT_COLUMN_WIDTH : 0;

  function toggleAll() {
    selection?.onChange(allSelected ? new Set() : new Set(selectableIds));
  }

  function toggleRow(id: string) {
    if (!selection) return;
    const next = new Set(selection.selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    selection.onChange(next);
  }

  const activeWidths =
    widths && columns.every((column) => typeof widths[column.key] === "number") ? widths : null;
  const fixedSum = activeWidths
    ? columns.slice(0, -1).reduce((sum, column) => sum + activeWidths[column.key], 0)
    : 0;
  const minTableWidth = activeWidths
    ? Math.max(640, fixedSum + selectWidth + MIN_COLUMN_WIDTH)
    : undefined;

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

  const region = (
    <div className="table-wrap" role="region" aria-label={label} tabIndex={0}>
      <table
        data-ui="table"
        className={["data-table", activeWidths && "resized", selection && "selectable"]
          .filter(Boolean)
          .join(" ")}
        style={minTableWidth !== undefined ? { minWidth: `${minTableWidth}px` } : undefined}
      >
        {activeWidths && (
          <colgroup>
            {selection && <col style={{ width: `${SELECT_COLUMN_WIDTH}px` }} />}
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
            {selection &&
              (selection.selectAllLabel && selectedCount === 0 ? (
                <th scope="col" className="col-select">
                  <RowCheck
                    label={selection.selectAllLabel}
                    checked={false}
                    disabled={selectableIds.length === 0}
                    onChange={toggleAll}
                  />
                </th>
              ) : (
                <td className="col-select" />
              ))}
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
              <td className="empty" colSpan={columns.length + (selection ? 1 : 0)}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row) => {
              const selectable = selection ? (selection.isSelectable?.(row) ?? true) : false;
              const selected = selectable && !!selection?.selectedIds.has(row.id);
              return (
                <tr key={row.id} className={selected ? "selected" : undefined}>
                  {selection && (
                    <td className="col-select">
                      {selectable && (
                        <RowCheck
                          label={selection.rowLabel(row)}
                          checked={selected}
                          onChange={() => toggleRow(row.id)}
                        />
                      )}
                    </td>
                  )}
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
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );

  if (!selection) return region;

  return (
    <div className="table-root">
      {region}
      {selectedCount > 0 && (
        <div
          className="table-selection-bar"
          role="region"
          aria-label={selection.selectedLabel(selectedCount)}
        >
          {selection.selectAllLabel && (
            <RowCheck
              label={selection.selectAllLabel}
              checked={allSelected}
              indeterminate={!allSelected}
              onChange={toggleAll}
            />
          )}
          <span className="table-selection-count">{selection.selectedLabel(selectedCount)}</span>
          {selection.actions && <div className="table-selection-actions">{selection.actions}</div>}
        </div>
      )}
    </div>
  );
}
