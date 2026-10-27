import { render, screen } from "@testing-library/react";
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
