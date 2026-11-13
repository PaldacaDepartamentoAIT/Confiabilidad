import { render, screen } from "@testing-library/react";

import { Fade } from "./Fade";

test("wraps its content in a container that carries the entry animation", () => {
  const { container } = render(
    <Fade fadeKey="a">
      <p>Content</p>
    </Fade>,
  );
  const wrapper = container.firstElementChild as HTMLElement;
  expect(wrapper).toHaveClass("public-fade");
  expect(wrapper).toContainElement(screen.getByText("Content"));
});

test("mounts its content again when the key changes, so the animation repeats", () => {
  const { container, rerender } = render(
    <Fade fadeKey="code">
      <input aria-label="Field" />
    </Fade>,
  );
  const before = container.firstElementChild;
  const input = screen.getByLabelText("Field");

  rerender(
    <Fade fadeKey="code">
      <input aria-label="Field" />
    </Fade>,
  );
  expect(container.firstElementChild).toBe(before);
  expect(screen.getByLabelText("Field")).toBe(input);

  rerender(
    <Fade fadeKey="password">
      <input aria-label="Field" />
    </Fade>,
  );
  expect(container.firstElementChild).not.toBe(before);
  expect(screen.getByLabelText("Field")).not.toBe(input);
});
