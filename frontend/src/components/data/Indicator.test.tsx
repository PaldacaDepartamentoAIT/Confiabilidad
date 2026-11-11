import { render, screen } from "@testing-library/react";
import axe from "axe-core";

import { Indicator, IndicatorGrid } from "./Indicator";

test("shows the label, the figure and the help inside a block marked as an indicator", () => {
  const { container } = render(<Indicator label="Assets" value="248" help="12 new this month" />);

  const indicator = container.firstElementChild;
  expect(indicator).toHaveAttribute("data-ui", "indicator");
  expect(indicator).toHaveClass("block", "kpi");
  expect(indicator).not.toHaveClass("featured");
  expect(indicator).not.toHaveClass("alert");
  expect(container.querySelector(".lab")).toHaveTextContent("Assets");
  expect(container.querySelector(".num")).toHaveTextContent("248");
  expect(container.querySelector(".help")).toHaveTextContent("12 new this month");
});

test("the help is optional", () => {
  const { container } = render(<Indicator label="Assets" value={248} />);
  expect(container.querySelector(".help")).not.toBeInTheDocument();
  expect(container.querySelector(".num")).toHaveTextContent("248");
});

test.each(["featured", "alert"] as const)("the %s variant adds its class", (variant) => {
  const { container } = render(<Indicator label="Assets" value="1" variant={variant} />);
  expect(container.firstElementChild).toHaveClass("block", "kpi", variant);
});

test("the grid lays out its indicators", () => {
  const { container } = render(
    <IndicatorGrid>
      <Indicator label="A" value="1" />
      <Indicator label="B" value="2" />
    </IndicatorGrid>,
  );
  const grid = container.firstElementChild;
  expect(grid).toHaveClass("kpis");
  expect(grid?.querySelectorAll("[data-ui='indicator']")).toHaveLength(2);
});

test("has no accessibility violations", async () => {
  const { container } = render(
    <IndicatorGrid>
      <Indicator label="A" value="1" help="x" />
      <Indicator label="B" value="2" variant="featured" />
      <Indicator label="C" value="3" variant="alert" />
    </IndicatorGrid>,
  );
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
