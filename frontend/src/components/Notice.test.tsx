import { render, screen } from "@testing-library/react";
import axe from "axe-core";

import { Notice } from "./Notice";

test("shows its text next to an information icon, as a status", () => {
  const { container } = render(<Notice>Saved draft</Notice>);

  const notice = screen.getByRole("status");
  expect(notice).toHaveClass("notice");
  expect(notice).toHaveTextContent("Saved draft");
  expect(notice).toHaveAttribute("data-ui", "notice");
  const icon = container.querySelector("svg");
  expect(icon).toHaveClass("lucide-info");
  expect(icon).toHaveAttribute("aria-hidden", "true");
});

test("the success kind uses a check icon", () => {
  const { container } = render(<Notice kind="success">Done</Notice>);
  expect(container.querySelector("svg")).toHaveClass("lucide-check");
});

test("the role can be changed, for example to read an error at once", () => {
  render(<Notice role="alert">Careful</Notice>);
  expect(screen.getByRole("alert")).toHaveTextContent("Careful");
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
});

test("extra attributes and class names reach the notice, and it can be hidden", () => {
  render(
    <Notice id="n1" className="wide" hidden>
      Hidden
    </Notice>,
  );
  const notice = document.getElementById("n1");
  expect(notice).toHaveClass("notice", "wide");
  expect(notice).toHaveAttribute("hidden");
});

test("has no accessibility violations with either icon", async () => {
  const { container } = render(
    <div>
      <Notice>One</Notice>
      <Notice kind="success">Two</Notice>
    </div>,
  );
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
