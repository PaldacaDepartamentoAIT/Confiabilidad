import { render, screen } from "@testing-library/react";
import axe from "axe-core";

import { TabPanel } from "./TabPanel";

test("is the tab panel of its tab, named by it, and shows its content when active", () => {
  render(
    <>
      <button role="tab" id="form-tab-location" aria-controls="form-panel-location">
        Ubicación
      </button>
      <TabPanel idPrefix="form" id="location" active>
        <p>Where it is</p>
      </TabPanel>
    </>,
  );

  const panel = screen.getByRole("tabpanel", { name: "Ubicación" });
  expect(panel).toHaveAttribute("id", "form-panel-location");
  expect(panel).toHaveAttribute("aria-labelledby", "form-tab-location");
  expect(panel).not.toHaveAttribute("hidden");
  expect(screen.getByText("Where it is")).toBeVisible();
});

test("is hidden when it is not the active one, so only one section is visible", () => {
  render(
    <>
      <TabPanel idPrefix="form" id="a" active={false}>
        <p>A</p>
      </TabPanel>
      <TabPanel idPrefix="form" id="b" active>
        <p>B</p>
      </TabPanel>
    </>,
  );

  expect(screen.getByText("B")).toBeVisible();
  expect(screen.getByText("A")).not.toBeVisible();
  expect(screen.getAllByRole("tabpanel")).toHaveLength(1);
});

test("does not fade in the first time it shows, only when it becomes active", () => {
  const { rerender } = render(
    <TabPanel idPrefix="form" id="a" active>
      A
    </TabPanel>,
  );
  expect(document.getElementById("form-panel-a")).not.toHaveClass("entering");

  rerender(
    <TabPanel idPrefix="form" id="a" active={false}>
      A
    </TabPanel>,
  );
  expect(document.getElementById("form-panel-a")).not.toHaveClass("entering");

  rerender(
    <TabPanel idPrefix="form" id="a" active>
      A
    </TabPanel>,
  );
  expect(document.getElementById("form-panel-a")).toHaveClass("entering");

  rerender(
    <TabPanel idPrefix="form" id="a" active={false}>
      A
    </TabPanel>,
  );
  expect(document.getElementById("form-panel-a")).not.toHaveClass("entering");
});

test("other class names and attributes reach the panel, and it can hold anything", () => {
  render(
    <TabPanel idPrefix="form" id="a" active className="stack" data-testid="p">
      <span>x</span>
    </TabPanel>,
  );
  const panel = screen.getByTestId("p");
  expect(panel).toHaveClass("stack");
  expect(panel).toHaveAttribute("role", "tabpanel");
});

test("has no accessibility violations", async () => {
  const { container } = render(
    <>
      <div role="tablist" aria-label="Sections">
        <button role="tab" id="form-tab-a" aria-controls="form-panel-a" aria-selected="true">
          A
        </button>
      </div>
      <TabPanel idPrefix="form" id="a" active>
        <p>Content</p>
      </TabPanel>
    </>,
  );
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});
