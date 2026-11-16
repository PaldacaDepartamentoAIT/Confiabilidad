import { render, screen } from "@testing-library/react";
import axe from "axe-core";

import { BarChart } from "./BarChart";
import type { ChartGroup } from "./chartScale";

const groups: ChartGroup[] = [
  { label: "Jun", first: 62, second: 48 },
  { label: "Jul", first: 70, second: 44 },
  { label: "Ago", first: 78, second: 38 },
  { label: "Sep", first: 84, second: 30 },
  { label: "Oct", first: 90, second: 26 },
  { label: "Nov", first: 96, second: 22 },
];

function renderChart(props: Partial<Parameters<typeof BarChart>[0]> = {}) {
  return render(
    <BarChart
      groups={groups}
      legend={{ first: "Preventive", second: "Corrective" }}
      description="Orders from June to November: preventive rise from 62 to 96."
      emptyMessage="No data"
      {...props}
    />,
  );
}

test("is an image with the description as its text alternative, scaled to its block", () => {
  renderChart();

  const chart = screen.getByRole("img", { name: /preventive rise from 62 to 96/ });
  expect(chart.tagName.toLowerCase()).toBe("svg");
  expect(chart).toHaveClass("chart");
  expect(chart).toHaveAttribute("viewBox", "0 0 640 240");
  expect(chart).toHaveAttribute("width", "100%");
  expect(chart).toHaveAttribute("data-ui", "bar-chart");
});

test("draws two bars per group: the first series in the primary color, the second in gray, without a border", () => {
  const { container } = renderChart();

  const first = container.querySelectorAll("rect[data-series='first']");
  const second = container.querySelectorAll("rect[data-series='second']");
  expect(first).toHaveLength(6);
  expect(second).toHaveLength(6);
  first.forEach((bar) => {
    expect(bar).toHaveAttribute("fill", "var(--primary)");
    expect(bar).not.toHaveAttribute("stroke");
  });
  second.forEach((bar) => {
    expect(bar).toHaveAttribute("fill", "var(--gray)");
    expect(bar).not.toHaveAttribute("stroke");
  });
});

test("the bars have the geometry of the guide: 30 px wide, a group every 96 px, height proportional to the axis", () => {
  const { container } = renderChart();

  const first = container.querySelector("rect[data-series='first']");
  const second = container.querySelector("rect[data-series='second']");
  // Primer grupo, con el eje de 0 a 120 y el área de 192 px de alto desde y = 8.
  expect(first).toHaveAttribute("x", "56");
  expect(first).toHaveAttribute("width", "30");
  expect(Number(first?.getAttribute("height"))).toBeCloseTo((62 / 120) * 192);
  expect(Number(first?.getAttribute("y"))).toBeCloseTo(8 + 192 - (62 / 120) * 192);
  expect(second).toHaveAttribute("x", "90");
  expect(container.querySelectorAll("rect[data-series='first']")[1]).toHaveAttribute("x", "152");
});

test("draws the grid behind the bars", () => {
  const { container } = renderChart();

  const grid = container.querySelector("rect[data-grid]");
  expect(grid).toHaveAttribute("x", "40");
  expect(grid).toHaveAttribute("y", "8");
  expect(grid).toHaveAttribute("width", "576");
  expect(grid).toHaveAttribute("height", "192");
  expect(grid?.getAttribute("fill")).toMatch(/^url\(#.+\)$/);
  const pattern = container.querySelector("pattern");
  expect(pattern).toHaveAttribute("width", "16");
  expect(pattern).toHaveAttribute("height", "16");
  expect(pattern?.querySelector("path")).toHaveAttribute("stroke", "var(--grid)");
  const bars = container.querySelector("rect[data-series]");
  expect(grid!.compareDocumentPosition(bars!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

test("the vertical axis has a number every 30 up to the next multiple that covers the data", () => {
  const { container } = renderChart();

  const ticks = [...container.querySelectorAll("text[data-tick]")];
  expect(ticks.map((tick) => tick.textContent)).toEqual(["0", "30", "60", "90", "120"]);
  ticks.forEach((tick) => {
    expect(tick).toHaveAttribute("x", "32");
    expect(tick).toHaveAttribute("text-anchor", "end");
  });
});

test("the group labels sit below the plot, centered on each group", () => {
  const { container } = renderChart();

  const labels = [...container.querySelectorAll("text[data-label]")];
  expect(labels.map((label) => label.textContent)).toEqual([
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
  ]);
  expect(labels[0]).toHaveAttribute("x", "88");
  expect(labels[0]).toHaveAttribute("y", "220");
  expect(labels[0]).toHaveAttribute("text-anchor", "middle");
});

test("the legend names both series with their swatch", () => {
  const { container } = renderChart();

  const items = container.querySelectorAll(".legend span");
  expect(items).toHaveLength(2);
  expect(items[0]).toHaveTextContent("Preventive");
  expect(items[1]).toHaveTextContent("Corrective");
  expect(items[0].querySelector("i")).toHaveStyle({ background: "var(--primary)" });
  expect(items[1].querySelector("i")).toHaveStyle({ background: "var(--gray)" });
});

test("the axis grows with the data", () => {
  const { container } = renderChart({ groups: [{ label: "A", first: 31, second: 0 }] });
  const ticks = [...container.querySelectorAll("text[data-tick]")].map((tick) => tick.textContent);
  expect(ticks).toEqual(["0", "30", "60"]);
});

test.each([
  ["no data", []],
  ["a negative value", [{ label: "A", first: -1, second: 2 }]],
  ["a value that is not a number", [{ label: "A", first: Number.NaN, second: 2 }]],
])("with %s it shows the empty message instead of the chart", (_name, data) => {
  const { container } = renderChart({ groups: data });

  expect(screen.getByText("No data")).toBeInTheDocument();
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
  expect(container.querySelector("svg")).not.toBeInTheDocument();
  expect(container.querySelector(".legend")).not.toBeInTheDocument();
});

test("two charts do not share the grid pattern", () => {
  const { container } = render(
    <>
      <BarChart
        groups={groups}
        legend={{ first: "A", second: "B" }}
        description="one"
        emptyMessage="-"
      />
      <BarChart
        groups={groups}
        legend={{ first: "A", second: "B" }}
        description="two"
        emptyMessage="-"
      />
    </>,
  );
  const ids = [...container.querySelectorAll("pattern")].map((pattern) => pattern.id);
  expect(new Set(ids).size).toBe(2);
});

test("has no accessibility violations with data and without it", async () => {
  const run = (container: HTMLElement) =>
    axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  const full = renderChart();
  expect((await run(full.container)).violations).toEqual([]);
  full.unmount();
  const empty = renderChart({ groups: [] });
  expect((await run(empty.container)).violations).toEqual([]);
});
