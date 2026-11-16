import { render, screen, within } from "@testing-library/react";
import axe from "axe-core";

import { StatusGrid, type StatusGridCell, type StatusGridLabels } from "./StatusGrid";

const labels: StatusGridLabels = {
  normal: "Normal",
  p1: "P1",
  p2: "P2",
  warning: "Warning",
  neutral: "Maintenance",
};

const cells: StatusGridCell[] = [
  { name: "A-100" },
  { name: "A-103", kind: "p2" },
  { name: "A-106", kind: "warning" },
  { name: "A-109", kind: "neutral" },
  { name: "A-112", kind: "p1" },
];

function renderGrid(props: Partial<Parameters<typeof StatusGrid>[0]> = {}) {
  return render(<StatusGrid label="Asset status" cells={cells} labels={labels} {...props} />);
}

test("is a named group with one cell per record, each an image with title and accessible label", () => {
  renderGrid();

  const grid = screen.getByRole("group", { name: "Asset status" });
  expect(grid).toHaveClass("cells");
  const images = within(grid).getAllByRole("img");
  expect(images).toHaveLength(5);
  expect(images.map((cell) => cell.getAttribute("aria-label"))).toEqual([
    "A-100 · Normal",
    "A-103 · P2",
    "A-106 · Warning",
    "A-109 · Maintenance",
    "A-112 · P1",
  ]);
  images.forEach((cell) => {
    expect(cell).toHaveClass("cell");
    expect(cell).toHaveAttribute("title", cell.getAttribute("aria-label"));
  });
});

test("each state has its class, and the normal cell has none", () => {
  renderGrid();

  const images = screen.getAllByRole("img");
  expect(images[0].className).toBe("cell");
  expect(images[1]).toHaveClass("cell", "p2");
  expect(images[2]).toHaveClass("cell", "warning");
  expect(images[3]).toHaveClass("cell", "neutral");
  expect(images[4]).toHaveClass("cell", "p1");
});

test("the alarm cells carry the glyph of their shape at 12 px, in the color of the canvas", () => {
  renderGrid();

  const [normal, p2, warning, neutral, p1] = screen.getAllByRole("img");
  expect(normal.querySelector("svg")).not.toBeInTheDocument();
  expect(neutral.querySelector("svg")).not.toBeInTheDocument();
  expect(p2.querySelector("[data-shape='triangle']")).toHaveAttribute("width", "12");
  expect(warning.querySelector("[data-shape='diamond']")).toBeInTheDocument();
  expect(p1.querySelector("[data-shape='square']")).toBeInTheDocument();
  [p2, warning, p1].forEach((cell) => {
    expect(cell.querySelector("svg")).toHaveStyle({ color: "var(--bg)" });
    expect(cell.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  });
});

test("the legend names the four states with their 16 px shape and the label in ink", () => {
  const { container } = renderGrid();

  const legend = container.querySelector(".legend");
  expect(legend).toHaveClass("cells-legend");
  const items = [...(legend?.querySelectorAll("span") ?? [])];
  expect(items.map((item) => item.textContent)).toEqual(["Maintenance", "P1", "P2", "Warning"]);
  expect(items.map((item) => item.querySelector("svg")?.getAttribute("data-shape"))).toEqual([
    "hollow-square",
    "square",
    "triangle",
    "diamond",
  ]);
  items.forEach((item) => expect(item.querySelector("svg")).toHaveAttribute("width", "16"));
});

test("without cells it shows an empty grid and still the legend", () => {
  const { container } = renderGrid({ cells: [] });
  expect(screen.queryAllByRole("img")).toHaveLength(0);
  expect(container.querySelector(".legend")).toBeInTheDocument();
});

test("has no accessibility violations", async () => {
  const { container } = renderGrid();
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
