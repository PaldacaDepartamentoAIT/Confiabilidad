import { render, screen } from "@testing-library/react";
import axe from "axe-core";

import { Block, Counter } from "./Block";

test("renders its content in a plain block marked for the design system", () => {
  const { container } = render(
    <Block>
      <p>Content</p>
    </Block>,
  );
  const block = container.firstElementChild;
  expect(block?.tagName).toBe("DIV");
  expect(block).toHaveClass("block");
  expect(block).not.toHaveClass("featured");
  expect(block).not.toHaveClass("alert");
  expect(block).not.toHaveClass("default");
  expect(block).toHaveAttribute("data-ui", "block");
  expect(screen.getByText("Content")).toBeInTheDocument();
  expect(container.querySelector(".blk-h")).not.toBeInTheDocument();
});

test.each([
  ["featured", "featured"],
  ["alert", "alert"],
] as const)("the %s variant adds its class", (variant, className) => {
  const { container } = render(<Block variant={variant}>x</Block>);
  expect(container.firstElementChild).toHaveClass("block", className);
});

test("shows a title as a level-2 heading in the block header", () => {
  const { container } = render(<Block title="Identification">x</Block>);
  const heading = screen.getByRole("heading", { level: 2, name: "Identification" });
  expect(heading).toHaveAttribute("data-ui", "block-title");
  expect(heading.parentElement).toHaveClass("blk-h");
  expect(container.firstElementChild).not.toHaveAttribute("aria-labelledby");
  expect(container.firstElementChild?.firstElementChild).toBe(heading.parentElement);
});

test("the heading level can be changed", () => {
  render(
    <Block title="Sub" headingLevel={3}>
      x
    </Block>,
  );
  expect(screen.getByRole("heading", { level: 3, name: "Sub" })).toBeInTheDocument();
});

test("shows a counter after the title and the actions pushed to the right", () => {
  const { container } = render(
    <Block title="Inventory" count={8} countLabel="8 assets" actions={<button>Add</button>}>
      x
    </Block>,
  );
  const header = container.querySelector(".blk-h");
  const children = [...(header?.children ?? [])];
  expect(children.map((child) => child.tagName)).toEqual(["H2", "SPAN", "SPAN", "BUTTON"]);
  expect(children[1]).toHaveClass("counter");
  expect(children[1]).toHaveTextContent("8");
  expect(children[1]).toHaveAttribute("aria-label", "8 assets");
  expect(children[1]).toHaveAttribute("data-ui", "counter");
  expect(children[2]).toHaveClass("sp");
  expect(screen.getByRole("button", { name: "Add" })).toBeInTheDocument();
});

test("a counter of zero is still shown", () => {
  render(
    <Block title="Empty" count={0}>
      x
    </Block>,
  );
  expect(screen.getByText("0")).toHaveClass("counter");
});

test("without title or counter, only actions are placed in the header", () => {
  const { container } = render(<Block actions={<button>Add</button>}>x</Block>);
  expect(container.querySelector(".blk-h")?.querySelector("h2")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Add" })).toBeInTheDocument();
});

test("as a section or aside it is a named region labelled by its title", () => {
  render(
    <Block as="aside" title="Summary" variant="featured">
      x
    </Block>,
  );
  const region = screen.getByRole("complementary", { name: "Summary" });
  expect(region).toHaveClass("block", "featured");
});

test("extra attributes and class names reach the block", () => {
  const { container } = render(
    <Block className="summary" id="b1" aria-live="polite">
      x
    </Block>,
  );
  const block = container.firstElementChild;
  expect(block).toHaveClass("block", "summary");
  expect(block).toHaveAttribute("id", "b1");
  expect(block).toHaveAttribute("aria-live", "polite");
});

test("Counter is a small gray counter", () => {
  render(<Counter>3</Counter>);
  expect(screen.getByText("3")).toHaveClass("counter");
});

test("has no accessibility violations in any variant", async () => {
  const { container } = render(
    <div>
      <Block title="One" count={1}>
        x
      </Block>
      <Block as="section" title="Two" variant="featured">
        x
      </Block>
      <Block as="aside" title="Three" variant="alert">
        x
      </Block>
    </div>,
  );
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
