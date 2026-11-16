import { render, screen } from "@testing-library/react";
import axe from "axe-core";

import { AlarmNotice } from "./AlarmNotice";
import type { AlarmKind } from "../icons/shapes";

const EXPECTED: [AlarmKind, string, string][] = [
  ["p1", "var(--p1)", "square"],
  ["p2", "var(--p2)", "triangle"],
  ["warning", "var(--warn)", "diamond"],
  ["neutral", "var(--text2)", "hollow-square"],
];

test.each(EXPECTED)("%s uses its own colour and shape", (kind, colour, shape) => {
  const { container } = render(<AlarmNotice kind={kind}>Text</AlarmNotice>);

  const notice = container.firstElementChild;
  expect(notice).toHaveClass("aviso");
  expect(notice).toHaveAttribute("data-ui", "alarm-notice");
  expect(notice?.getAttribute("style")).toContain(`--c: ${colour}`);
  const shapeElement = notice?.querySelector("svg");
  expect(shapeElement).toHaveAttribute("data-shape", shape);
  expect(shapeElement).toHaveAttribute("aria-hidden", "true");
});

test("shows the title in bold followed by the text, both in ink", () => {
  render(
    <AlarmNotice kind="p1" title="P1">
      High pressure on compressor C-102.
    </AlarmNotice>,
  );

  const title = screen.getByText("P1");
  expect(title.tagName).toBe("B");
  expect(title.parentElement).toHaveClass("tx");
  expect(title.parentElement).toHaveTextContent("P1 High pressure on compressor C-102.");
});

test("works without a title", () => {
  const { container } = render(<AlarmNotice kind="warning">Only text</AlarmNotice>);
  expect(container.querySelector("b")).not.toBeInTheDocument();
  expect(container.querySelector(".tx")).toHaveTextContent("Only text");
});

test("places an optional action after the text", () => {
  const { container } = render(
    <AlarmNotice kind="p2" action={<button type="button">View alarm</button>}>
      Text
    </AlarmNotice>,
  );

  const children = [...(container.firstElementChild?.children ?? [])].map((child) => child.tagName);
  expect(children).toEqual(["svg", "DIV", "BUTTON"]);
  expect(screen.getByRole("button", { name: "View alarm" })).toBeInTheDocument();
});

test("has no role unless it is given one, and extra attributes reach it", () => {
  const { container, rerender } = render(<AlarmNotice kind="p1">Text</AlarmNotice>);
  expect(container.firstElementChild).not.toHaveAttribute("role");

  rerender(
    <AlarmNotice kind="p1" role="alert" id="a1" className="wide">
      Text
    </AlarmNotice>,
  );
  expect(screen.getByRole("alert")).toHaveAttribute("id", "a1");
  expect(screen.getByRole("alert")).toHaveClass("aviso", "wide");
});

test("has no accessibility violations", async () => {
  const { container } = render(
    <div>
      <AlarmNotice kind="p1" title="P1" action={<button type="button">View alarm</button>}>
        Text
      </AlarmNotice>
      <AlarmNotice kind="neutral" role="status">
        Maintenance
      </AlarmNotice>
    </div>,
  );
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});

test("a style passed in wins over the colour of the kind and keeps the rest", () => {
  const { container } = render(
    <AlarmNotice kind="p1" style={{ "--c": "red", marginTop: "4px" } as React.CSSProperties}>
      Text
    </AlarmNotice>,
  );
  const style = container.firstElementChild?.getAttribute("style");
  expect(style).toContain("--c: red");
  expect(style).toContain("margin-top: 4px");
  expect(style).not.toContain("var(--p1)");
});
