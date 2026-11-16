import { render, screen } from "@testing-library/react";
import axe from "axe-core";

import { Chip } from "./Chip";

test("renders its text in a chip marked for the design system", () => {
  render(<Chip>Critical</Chip>);
  const chip = screen.getByText("Critical");
  expect(chip.tagName).toBe("SPAN");
  expect(chip).toHaveClass("chip");
  expect(chip).toHaveAttribute("data-ui", "chip");
});

test("extra attributes and class names reach the chip", () => {
  render(
    <Chip className="extra" title="Criticality" lang="en">
      A
    </Chip>,
  );
  const chip = screen.getByText("A");
  expect(chip).toHaveClass("chip", "extra");
  expect(chip).toHaveAttribute("title", "Criticality");
  expect(chip).toHaveAttribute("lang", "en");
});

test("has no accessibility violations", async () => {
  const { container } = render(<Chip>High</Chip>);
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
