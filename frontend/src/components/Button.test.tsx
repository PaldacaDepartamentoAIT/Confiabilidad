import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Button } from "./Button";

test("its accessible name is its visible text", () => {
  render(<Button>Verify</Button>);

  expect(screen.getByRole("button", { name: "Verify" })).toHaveTextContent("Verify");
});

test("is a plain button unless told to submit", () => {
  render(
    <>
      <Button>Plain</Button>
      <Button type="submit">Send</Button>
    </>,
  );

  expect(screen.getByRole("button", { name: "Plain" })).toHaveAttribute("type", "button");
  expect(screen.getByRole("button", { name: "Send" })).toHaveAttribute("type", "submit");
});

test("is activated by click, Enter and Space", async () => {
  const user = userEvent.setup();
  const onClick = vi.fn();
  render(<Button onClick={onClick}>Verify</Button>);

  await user.click(screen.getByRole("button", { name: "Verify" }));
  await user.keyboard("{Enter}");
  await user.keyboard(" ");

  expect(onClick).toHaveBeenCalledTimes(3);
});

test("with keepFocusOnMouseDown, pressing it with the mouse leaves the focus where it was", async () => {
  const user = userEvent.setup();
  const onClick = vi.fn();
  render(
    <>
      <input aria-label="Field" />
      <Button keepFocusOnMouseDown onClick={onClick}>
        Verify
      </Button>
    </>,
  );

  const field = screen.getByRole("textbox", { name: "Field" });
  await user.click(field);
  await user.click(screen.getByRole("button", { name: "Verify" }));

  expect(field).toHaveFocus();
  expect(onClick).toHaveBeenCalledTimes(1);
  expect(fireEvent.mouseDown(screen.getByRole("button", { name: "Verify" }))).toBe(false);
});

test("without keepFocusOnMouseDown, the mouse moves the focus to the button", () => {
  render(<Button>Verify</Button>);

  expect(fireEvent.mouseDown(screen.getByRole("button", { name: "Verify" }))).toBe(true);
});

test("keepFocusOnMouseDown does not change the keyboard", async () => {
  const user = userEvent.setup();
  const onClick = vi.fn();
  render(
    <Button keepFocusOnMouseDown onClick={onClick}>
      Verify
    </Button>,
  );

  await user.tab();
  expect(screen.getByRole("button", { name: "Verify" })).toHaveFocus();
  await user.keyboard("{Enter}");

  expect(onClick).toHaveBeenCalledTimes(1);
});

test("still calls its own onMouseDown when keeping the focus", () => {
  const onMouseDown = vi.fn();
  render(
    <Button keepFocusOnMouseDown onMouseDown={onMouseDown}>
      Verify
    </Button>,
  );

  fireEvent.mouseDown(screen.getByRole("button", { name: "Verify" }));

  expect(onMouseDown).toHaveBeenCalledTimes(1);
});
