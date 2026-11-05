import { render, screen } from "@testing-library/react";

import { FieldShell } from "./FieldShell";

function renderShell(props: Partial<Parameters<typeof FieldShell>[0]> = {}) {
  return render(
    <FieldShell id="f" label="Nombre" {...props}>
      {(description) => <input id="f" aria-describedby={description} />}
    </FieldShell>,
  );
}

test("the name goes before the control, with a hidden asterisk when required", () => {
  renderShell({ required: true });

  const label = screen.getByText("Nombre", { selector: "label" });
  const input = screen.getByRole("textbox", { name: "Nombre" });
  expect(label.compareDocumentPosition(input) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  const asterisk = screen.getByText("*");
  expect(asterisk).toHaveAttribute("aria-hidden", "true");
  expect(asterisk.closest("label")).toBe(label);
});

test("an optional field has no asterisk", () => {
  renderShell();

  expect(screen.queryByText("*")).not.toBeInTheDocument();
});

test("the error slot is always there, empty without an error", () => {
  const { container, rerender } = renderShell();

  const slot = container.querySelector(".field__error-slot");
  expect(slot).toBeInTheDocument();
  expect(slot).toBeEmptyDOMElement();

  rerender(
    <FieldShell id="f" label="Nombre" error="Escribe tu nombre.">
      {(description) => <input id="f" aria-describedby={description} />}
    </FieldShell>,
  );

  expect(container.querySelector(".field__error-slot")).toBe(slot);
  expect(slot).toHaveTextContent("Escribe tu nombre.");
  expect(screen.getByRole("textbox")).toHaveAccessibleDescription("Escribe tu nombre.");
});

test("the visible hint and the error describe the control together", () => {
  renderShell({ hint: "Como en tu documento.", error: "Escribe tu nombre." });

  expect(screen.getByText("Como en tu documento.")).toBeVisible();
  expect(screen.getByRole("textbox")).toHaveAccessibleDescription(
    "Como en tu documento. Escribe tu nombre.",
  );
});

test("without a hint or an error, the control has no description", () => {
  renderShell();

  expect(screen.getByRole("textbox")).not.toHaveAttribute("aria-describedby");
});

test("a hint alone describes the control", () => {
  renderShell({ hint: "Como en tu documento." });

  expect(screen.getByRole("textbox")).toHaveAccessibleDescription("Como en tu documento.");
});

test("a control inside the field goes after the input, in the same box", () => {
  const { container } = renderShell({ adornment: <button type="button">Ver</button> });

  const box = container.querySelector(".field__control");
  expect(box).toHaveClass("field__control--adorned");
  expect(box).toContainElement(screen.getByRole("textbox"));
  expect(box).toContainElement(screen.getByRole("button", { name: "Ver" }));
});

test("without a control inside, the box has no room reserved for it", () => {
  const { container } = renderShell();

  expect(container.querySelector(".field__control")).not.toHaveClass("field__control--adorned");
});
