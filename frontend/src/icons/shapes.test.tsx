import { render, screen } from "@testing-library/react";
import axe from "axe-core";

import { AlarmShape, type AlarmKind } from "./shapes";

const EXPECTED: Record<AlarmKind, { shape: string; color: string; filled: boolean }> = {
  p1: { shape: "square", color: "var(--p1)", filled: true },
  p2: { shape: "triangle", color: "var(--p2)", filled: true },
  warning: { shape: "diamond", color: "var(--warn)", filled: true },
  neutral: { shape: "hollow-square", color: "var(--text2)", filled: false },
};

test.each(Object.entries(EXPECTED) as [AlarmKind, (typeof EXPECTED)[AlarmKind]][])(
  "%s is drawn as a %s in its own colour",
  (kind, { shape, color, filled }) => {
    const { container } = render(<AlarmShape kind={kind} />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("data-shape", shape);
    expect(svg?.getAttribute("style")).toContain(`color: ${color}`);
    expect(svg).toHaveAttribute("viewBox", "0 0 16 16");
    expect(svg).toHaveAttribute("width", "16");
    expect(svg).toHaveAttribute("height", "16");
    if (filled) {
      expect(svg?.querySelector("[fill='currentColor']")).toBeInTheDocument();
    } else {
      const outline = svg?.querySelector("rect");
      expect(outline).toHaveAttribute("fill", "none");
      expect(outline).toHaveAttribute("stroke", "currentColor");
      expect(outline).toHaveAttribute("stroke-width", "2");
    }
  },
);

test("the four shapes draw different geometry, so colour is never the only cue", () => {
  const drawings = (Object.keys(EXPECTED) as AlarmKind[]).map(
    (kind) => render(<AlarmShape kind={kind} />).container.querySelector("svg")?.innerHTML,
  );
  expect(new Set(drawings).size).toBe(4);
});

test("draws the geometry of the reference screens", () => {
  const inner = (kind: AlarmKind) =>
    render(<AlarmShape kind={kind} />).container.querySelector("svg")?.innerHTML;
  expect(inner("p2")).toContain('d="M8 2 15 14H1z"');
  expect(inner("warning")).toContain('d="M8 1 15 8 8 15 1 8z"');
  expect(inner("p1")).toContain('width="12"');
});

test("is hidden from screen readers unless it has a label", () => {
  const { container, rerender } = render(<AlarmShape kind="p1" />);
  expect(container.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  expect(container.querySelector("svg")).not.toHaveAttribute("role");

  rerender(<AlarmShape kind="p1" label="Priority 1" />);
  expect(screen.getByRole("img", { name: "Priority 1" })).toBeInTheDocument();
  expect(container.querySelector("svg")).not.toHaveAttribute("aria-hidden");
});

test("a size, a class name and a colour can be overridden", () => {
  const { container } = render(
    <AlarmShape kind="p2" size={24} className="mark" style={{ color: "red" }} />,
  );
  const svg = container.querySelector("svg");
  expect(svg).toHaveAttribute("width", "24");
  expect(svg).toHaveAttribute("height", "24");
  expect(svg).toHaveClass("shape", "mark");
  expect(svg?.getAttribute("style")).toContain("color: red");
  expect(svg?.getAttribute("style")).not.toContain("var(--p2)");
});

test("has no accessibility violations with and without a label", async () => {
  const { container } = render(
    <div>
      <AlarmShape kind="p1" />
      <AlarmShape kind="neutral" label="Maintenance" />
    </div>,
  );
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
