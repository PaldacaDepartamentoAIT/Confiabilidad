import { render, screen } from "@testing-library/react";
import axe from "axe-core";

import { PublicPage } from "./PublicPage";

test("is the main region of the page, with one block that has the title as its level-1 heading", () => {
  const { container } = render(
    <PublicPage title="Register">
      <p>Content</p>
    </PublicPage>,
  );

  const main = screen.getByRole("main");
  expect(main).toHaveClass("public-page");
  const heading = screen.getByRole("heading", { level: 1, name: "Register" });
  expect(heading).toHaveAttribute("data-ui", "block-title");
  const block = container.querySelector(".block");
  expect(block).toHaveClass("public-card");
  expect(block).toHaveAttribute("data-ui", "block");
  expect(main).toContainElement(block as HTMLElement);
  expect(block).toContainElement(heading);
  expect(heading.parentElement).toHaveClass("blk-h");
  expect(block).toContainElement(screen.getByText("Content"));
});

test("the title goes before the content", () => {
  render(
    <PublicPage title="Register">
      <p>Content</p>
    </PublicPage>,
  );
  const heading = screen.getByRole("heading", { level: 1 });
  const content = screen.getByText("Content");
  expect(heading.compareDocumentPosition(content) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

test("the title can have an id, so that a form can be named by it", () => {
  render(
    <PublicPage title="Register" titleId="register-title">
      <form aria-labelledby="register-title" />
    </PublicPage>,
  );
  expect(screen.getByRole("heading", { level: 1 })).toHaveAttribute("id", "register-title");
  expect(screen.getByRole("form", { name: "Register" })).toBeInTheDocument();
});

test("without an id the heading has none", () => {
  render(<PublicPage title="Register">x</PublicPage>);
  expect(screen.getByRole("heading", { level: 1 })).not.toHaveAttribute("id");
});

test("has no accessibility violations", async () => {
  const { container } = render(
    <PublicPage title="Register">
      <p>Content</p>
    </PublicPage>,
  );
  const results = await axe.run(container, {
    rules: { "color-contrast": { enabled: false }, region: { enabled: false } },
  });
  expect(results.violations).toEqual([]);
});
