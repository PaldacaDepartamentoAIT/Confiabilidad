import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";

import { Checkbox } from "./Checkbox";

test("draws the box and its check inside the label, marked for the design system", () => {
  const { container } = render(<Checkbox label="Active company" />);

  const label = container.querySelector("label");
  expect(label).toHaveClass("check");
  const box = screen.getByRole("checkbox", { name: "Active company" });
  expect(box).toHaveAttribute("data-ui", "checkbox");
  expect(box.parentElement).toHaveClass("cb");
  expect(label).toContainElement(box);
  const icon = box.nextElementSibling;
  expect(icon).toHaveClass("lucide-check");
  expect(icon).toHaveAttribute("width", "14");
  expect(icon).toHaveAttribute("stroke-width", "3");
  expect(icon).toHaveAttribute("aria-hidden", "true");
  expect(label?.querySelector(".txt")).toHaveTextContent("Active company");
});

test("toggles with a click on the label and with the space bar", async () => {
  const user = userEvent.setup();
  render(<Checkbox label="Active company" />);
  const box = screen.getByRole("checkbox", { name: "Active company" });

  await user.click(screen.getByText("Active company"));
  expect(box).toBeChecked();
  await user.keyboard(" ");
  expect(box).not.toBeChecked();
});

test("a hint and an error go under the text with their own style and describe the box", () => {
  render(<Checkbox label="Accept" hint="Read them first." error="Accept the terms." />);

  const box = screen.getByRole("checkbox", { name: "Accept" });
  expect(box).toHaveAccessibleDescription("Read them first. Accept the terms.");
  expect(screen.getByText("Read them first.")).toHaveClass("help", "check-note");
  const error = screen.getByText("Accept the terms.").closest("p");
  expect(error).toHaveClass("error-msg", "check-note");
  expect(error?.querySelector("svg")).toHaveClass("lucide-circle-alert");
});

test("the required asterisk is part of the label text and hidden from screen readers", () => {
  render(<Checkbox label="Accept" required />);
  expect(screen.getByText("*")).toHaveAttribute("aria-hidden", "true");
  expect(screen.getByText("*").closest("label")).toHaveClass("check");
});

test("the label can be rich content", () => {
  render(<Checkbox label={<strong>Bold label</strong>} />);
  expect(screen.getByRole("checkbox", { name: "Bold label" })).toBeInTheDocument();
});

test("has no accessibility violations unchecked, checked and in error", async () => {
  const { container } = render(
    <div>
      <Checkbox label="One" />
      <Checkbox label="Two" defaultChecked hint="Help" />
      <Checkbox label="Three" error="Required" required />
    </div>,
  );
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
