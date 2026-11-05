import { render, screen } from "@testing-library/react";

import { MessageZone } from "./MessageZone";

test("the zone is there without a message", () => {
  const { container } = render(<MessageZone />);

  const zone = container.querySelector(".message-zone");
  expect(zone).toBeInTheDocument();
  expect(zone).toBeEmptyDOMElement();
});

test("the zone holds its messages", () => {
  const { container } = render(
    <MessageZone>
      <p>El código caduca en 12:30.</p>
    </MessageZone>,
  );

  expect(container.querySelector(".message-zone")).toContainElement(
    screen.getByText("El código caduca en 12:30."),
  );
});
