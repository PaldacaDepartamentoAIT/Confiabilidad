import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { useState } from "react";

import { Chip } from "../Chip";
import { Table, type TableColumn, type TableRow } from "./Table";

const columns: TableColumn[] = [
  { key: "code", header: "Code", kind: "code" },
  { key: "name", header: "Name" },
  { key: "criticality", header: "Criticality" },
  { key: "status", header: "Status", kind: "status" },
];

const rows: TableRow[] = [
  {
    id: "c-102",
    cells: {
      code: "C-102",
      name: "Air compressor",
      criticality: <Chip>High</Chip>,
      status: { text: "Out of service", kind: "p1" },
    },
  },
  {
    id: "v-033",
    cells: {
      code: "V-033",
      name: "Control valve",
      criticality: <Chip>Low</Chip>,
      status: { text: "Operating" },
    },
  },
];

function renderTable(props: Partial<Parameters<typeof Table>[0]> = {}) {
  return render(
    <Table label="Assets" columns={columns} rows={rows} emptyMessage="No assets" {...props} />,
  );
}

test("renders a header cell per column and a row per record, marked for the design system", () => {
  renderTable();

  const table = screen.getByRole("table");
  expect(table).toHaveAttribute("data-ui", "table");
  const headers = within(table).getAllByRole("columnheader");
  expect(headers.map((header) => header.textContent)).toEqual([
    "Code",
    "Name",
    "Criticality",
    "Status",
  ]);
  headers.forEach((header) => expect(header).toHaveAttribute("scope", "col"));
  expect(within(table).getAllByRole("row")).toHaveLength(3);
  expect(screen.getByText("Air compressor")).toBeInTheDocument();
  expect(screen.getByText("High")).toHaveAttribute("data-ui", "chip");
});

test("code columns use the monospaced class and text columns do not", () => {
  renderTable();

  expect(screen.getByRole("cell", { name: "C-102" })).toHaveClass("mono");
  expect(screen.getByRole("cell", { name: "Air compressor" })).not.toHaveClass("mono");
});

test("a status cell shows the shape of its priority beside the text, which has no color of its own", () => {
  renderTable();

  const cell = screen.getByRole("cell", { name: "Out of service" });
  const status = cell.querySelector(".st");
  expect(status?.querySelector("[data-shape='square']")).toBeInTheDocument();
  expect(status).toHaveTextContent("Out of service");
  expect(status?.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
});

test("the normal status shows no icon but reserves the same space", () => {
  renderTable();

  const status = screen.getByRole("cell", { name: "Operating" }).querySelector(".st");
  expect(status?.querySelector("svg")).not.toBeInTheDocument();
  expect(status?.firstElementChild).toHaveClass("shape");
  expect(status?.firstElementChild).toHaveAttribute("aria-hidden", "true");
});

test("the table scrolls horizontally inside a named, focusable region", () => {
  const { container } = renderTable();

  const region = screen.getByRole("region", { name: "Assets" });
  expect(region).toHaveClass("table-wrap");
  expect(region).toHaveAttribute("tabindex", "0");
  expect(region).toContainElement(screen.getByRole("table"));
  expect(container.firstElementChild).toBe(region);
});

test("without rows it shows the empty message instead of the rows", () => {
  renderTable({ rows: [] });

  expect(screen.getAllByRole("row")).toHaveLength(2);
  const message = screen.getByRole("cell", { name: "No assets" });
  expect(message).toHaveAttribute("colspan", "4");
  expect(message).toHaveClass("empty");
  expect(screen.getAllByRole("columnheader")).toHaveLength(4);
});

test("with rows it does not show the empty message", () => {
  renderTable();
  expect(screen.queryByText("No assets")).not.toBeInTheDocument();
});

function SelectableTable({
  isSelectable,
  rowsOverride = rows,
  selectAllLabel = "Select all assets",
}: {
  isSelectable?: (row: TableRow) => boolean;
  rowsOverride?: TableRow[];
  selectAllLabel?: string;
}) {
  const [selectedIds, setSelectedIds] = useState<ReadonlySet<string>>(new Set());
  return (
    <Table
      label="Assets"
      columns={columns}
      rows={rowsOverride}
      emptyMessage="No assets"
      selection={{
        selectedIds,
        onChange: setSelectedIds,
        isSelectable,
        selectAllLabel,
        rowLabel: (row) => `Select ${row.id}`,
        selectedLabel: (count) => `${count} selected`,
        actions: <button type="button">Delete selected</button>,
      }}
    />
  );
}

test("selection: the header checkbox selects and clears all rows and the overlay bar shows the checkbox, count and actions", async () => {
  const user = userEvent.setup();
  render(<SelectableTable />);

  const initialAll = screen.getByRole("checkbox", { name: "Select all assets" });
  expect(initialAll).not.toBeChecked();
  expect(screen.queryByRole("button", { name: "Delete selected" })).not.toBeInTheDocument();
  expect(screen.getAllByRole("checkbox")).toHaveLength(3);

  await user.click(initialAll);
  const bar = screen.getByRole("region", { name: "2 selected" });
  const overlayAll = within(bar).getByRole("checkbox", { name: "Select all assets" });
  expect(overlayAll).toBeChecked();
  expect(screen.getAllByRole("checkbox")).toHaveLength(3);
  expect(screen.getByRole("checkbox", { name: "Select c-102" })).toBeChecked();
  expect(screen.getByRole("checkbox", { name: "Select v-033" })).toBeChecked();
  expect(within(bar).getByText("2 selected")).toBeInTheDocument();
  expect(within(bar).getByRole("button", { name: "Delete selected" })).toBeInTheDocument();
  expect(screen.getByRole("cell", { name: "C-102" }).closest("tr")).toHaveClass("selected");

  await user.click(overlayAll);
  expect(screen.getByRole("checkbox", { name: "Select c-102" })).not.toBeChecked();
  expect(screen.queryByRole("region", { name: /selected/ })).not.toBeInTheDocument();
});

test("selection: a partial selection leaves the header checkbox indeterminate and a row can be unmarked", async () => {
  const user = userEvent.setup();
  render(<SelectableTable />);

  await user.click(screen.getByRole("checkbox", { name: "Select c-102" }));
  const allPartial = screen.getByRole("checkbox", {
    name: "Select all assets",
  }) as HTMLInputElement;
  expect(allPartial).not.toBeChecked();
  expect(allPartial.indeterminate).toBe(true);
  expect(screen.getByRole("button", { name: "Delete selected" })).toBeInTheDocument();

  await user.click(screen.getByRole("checkbox", { name: "Select v-033" }));
  const allFull = screen.getByRole("checkbox", { name: "Select all assets" }) as HTMLInputElement;
  expect(allFull).toBeChecked();
  expect(allFull.indeterminate).toBe(false);

  await user.click(screen.getByRole("checkbox", { name: "Select c-102" }));
  await user.click(screen.getByRole("checkbox", { name: "Select v-033" }));
  expect(screen.queryByRole("button", { name: "Delete selected" })).not.toBeInTheDocument();
});

test("selection: rows that are not selectable have no checkbox and are skipped by select all", async () => {
  const user = userEvent.setup();
  render(<SelectableTable isSelectable={(row) => row.id !== "c-102"} />);

  expect(screen.queryByRole("checkbox", { name: "Select c-102" })).not.toBeInTheDocument();
  await user.click(screen.getByRole("checkbox", { name: "Select all assets" }));

  expect(screen.getByRole("checkbox", { name: "Select v-033" })).toBeChecked();
  expect(screen.getByRole("checkbox", { name: "Select all assets" })).toBeChecked();
  expect(screen.getByRole("cell", { name: "C-102" }).closest("tr")).not.toHaveClass("selected");
});

test("selection: with no selectable rows the header checkbox is disabled and the empty message spans every column", () => {
  render(<SelectableTable rowsOverride={[]} />);

  expect(screen.getByRole("checkbox", { name: "Select all assets" })).toBeDisabled();
  expect(screen.getByRole("cell", { name: "No assets" })).toHaveAttribute("colspan", "5");
});

test("selection: the table keeps its first resize snapshot aligned with the checkbox column", () => {
  const { container } = render(<SelectableTable />);
  const headers = within(screen.getByRole("table")).getAllByRole("columnheader");
  const handle = headers[1].querySelector(".col-resize") as HTMLElement;

  fireEvent.mouseDown(handle, { clientX: 100 });
  fireEvent.mouseUp(window);

  const cols = container.querySelectorAll("colgroup col");
  expect(cols).toHaveLength(5);
  expect(cols[0]).toHaveStyle({ width: "44px" });
  expect(cols[4].getAttribute("style")).toBeNull();
});

test("selection: without selectAllLabel the header has no checkbox, row selection still shows the bottom bar and passes axe", async () => {
  const user = userEvent.setup();
  const { container } = render(<SelectableTable selectAllLabel="" />);

  expect(screen.queryByRole("checkbox", { name: "Select all assets" })).not.toBeInTheDocument();
  expect(screen.getAllByRole("checkbox")).toHaveLength(2);
  await user.click(screen.getByRole("checkbox", { name: "Select c-102" }));
  expect(screen.getByRole("region", { name: "1 selected" })).toBeInTheDocument();
  expect(
    (await axe.run(container, { rules: { "color-contrast": { enabled: false } } })).violations,
  ).toEqual([]);
});

test("selection: has no accessibility violations with and without a selection", async () => {
  const user = userEvent.setup();
  const { container } = render(<SelectableTable />);
  const run = () => axe.run(container, { rules: { "color-contrast": { enabled: false } } });

  expect((await run()).violations).toEqual([]);
  await user.click(screen.getByRole("checkbox", { name: "Select all assets" }));
  expect((await run()).violations).toEqual([]);
});

test("has no accessibility violations with rows and without them", async () => {
  const run = (container: HTMLElement) =>
    axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  const full = renderTable();
  expect((await run(full.container)).violations).toEqual([]);
  full.unmount();
  const empty = renderTable({ rows: [] });
  expect((await run(empty.container)).violations).toEqual([]);
});

test("resizes columns by dragging the border handle, clamps to minimum width and keeps ellipsis wrappers", () => {
  const { container } = renderTable();
  const table = screen.getByRole("table");
  const headers = within(table).getAllByRole("columnheader");
  headers.forEach((header, index) => {
    vi.spyOn(header, "getBoundingClientRect").mockReturnValue({
      width: index === 1 ? 200 : 120,
      height: 36,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });
  });

  const handle = headers[1].querySelector(".col-resize") as HTMLElement;
  expect(handle).toHaveAttribute("aria-hidden", "true");
  expect(headers[headers.length - 1].querySelector(".col-resize")).toBeNull();

  fireEvent.mouseDown(handle, { clientX: 200 });
  expect(headers[1]).toHaveClass("resizing");
  expect(table).toHaveClass("resized");

  fireEvent.mouseMove(window, { clientX: 260 });
  const cols = container.querySelectorAll("colgroup col");
  expect(cols).toHaveLength(4);
  expect(cols[1]).toHaveStyle({ width: "260px" });
  expect(cols[3].getAttribute("style")).toBeNull();
  expect(table).toHaveStyle({ minWidth: "640px" });
  expect(table.style.width).toBe("");

  fireEvent.mouseMove(window, { clientX: 0 });
  expect(cols[1]).toHaveStyle({ width: "48px" });

  fireEvent.mouseUp(window);
  expect(headers[1]).not.toHaveClass("resizing");
  expect(headers[1].querySelector(".th-label")).toHaveTextContent("Name");
  expect(container.querySelector(".st-text")).toHaveTextContent("Out of service");
});
