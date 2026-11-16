import { render, screen, within } from "@testing-library/react";
import axe from "axe-core";

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

test("has no accessibility violations with rows and without them", async () => {
  const run = (container: HTMLElement) =>
    axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  const full = renderTable();
  expect((await run(full.container)).violations).toEqual([]);
  full.unmount();
  const empty = renderTable({ rows: [] });
  expect((await run(empty.container)).violations).toEqual([]);
});
