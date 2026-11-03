import { render, screen } from "@testing-library/react";
import axe from "axe-core";
import { createRef } from "react";

import { Checkbox } from "./Checkbox";
import { SelectField } from "./SelectField";

const options = [
  { value: "BR", label: "Brazil" },
  { value: "CL", label: "Chile" },
];

describe("casilla", () => {
  it("se nombra por su etiqueta y marca el obligatorio", () => {
    render(<Checkbox label="I accept the terms" required name="terms" />);

    const box = screen.getByRole("checkbox", { name: "I accept the terms" });
    expect(box).toHaveAttribute("aria-required", "true");
    expect(box).toHaveAttribute("name", "terms");
    expect(screen.getByText("*")).toHaveAttribute("aria-hidden", "true");
    expect(screen.getByText("*").closest("label")).not.toBeNull();
  });

  it("sin obligatorio no lleva asterisco ni aria-required", () => {
    render(<Checkbox label="Send me news" />);

    expect(screen.getByRole("checkbox", { name: "Send me news" })).not.toHaveAttribute(
      "aria-required",
    );
    expect(screen.queryByText("*")).not.toBeInTheDocument();
  });

  it("enlaza la ayuda y el error y se marca como inválida", () => {
    const { rerender } = render(
      <Checkbox label="I accept" hint="Read them first." error="Accept the terms." />,
    );

    const box = screen.getByRole("checkbox", { name: "I accept" });
    expect(box).toHaveAttribute("aria-invalid", "true");
    expect(box).toHaveAccessibleDescription("Read them first. Accept the terms.");

    rerender(<Checkbox label="I accept" />);

    expect(box).not.toHaveAttribute("aria-invalid");
    expect(box).not.toHaveAttribute("aria-describedby");
  });

  it("pasa su ref a la casilla", () => {
    const ref = createRef<HTMLInputElement>();
    render(<Checkbox ref={ref} label="I accept" />);

    expect(ref.current).toBe(screen.getByRole("checkbox", { name: "I accept" }));
  });
});

describe("selector", () => {
  it("se nombra por su etiqueta, ofrece las opciones y una vacía para elegir", () => {
    render(
      <SelectField label="Country" placeholder="Choose" options={options} required name="c" />,
    );

    const select = screen.getByRole("combobox", { name: "Country" });
    expect(select).toHaveAttribute("aria-required", "true");
    expect(select).toHaveAttribute("name", "c");
    expect(select).toHaveValue("");
    const items = screen.getAllByRole("option");
    expect(items.map((item) => [item.getAttribute("value"), item.textContent])).toEqual([
      ["", "Choose"],
      ["BR", "Brazil"],
      ["CL", "Chile"],
    ]);
    expect(screen.getByText("*").closest("label")).not.toBeNull();
  });

  it("enlaza la ayuda y el error y se marca como inválido", () => {
    const { rerender } = render(
      <SelectField
        label="Country"
        placeholder="Choose"
        options={options}
        hint="Where you live."
        error="Choose one."
      />,
    );

    const select = screen.getByRole("combobox", { name: "Country" });
    expect(select).toHaveAttribute("aria-invalid", "true");
    expect(select).toHaveAccessibleDescription("Where you live. Choose one.");

    rerender(<SelectField label="Country" placeholder="Choose" options={options} />);

    expect(select).not.toHaveAttribute("aria-invalid");
    expect(select).not.toHaveAttribute("aria-describedby");
    expect(select).not.toHaveAttribute("aria-required");
  });

  it("pasa su ref al selector", () => {
    const ref = createRef<HTMLSelectElement>();
    render(<SelectField ref={ref} label="Country" placeholder="Choose" options={options} />);

    expect(ref.current).toBe(screen.getByRole("combobox", { name: "Country" }));
  });
});

it("axe no encuentra fallos en la casilla ni en el selector con error", async () => {
  const { container } = render(
    <form>
      <Checkbox label="I accept" required error="Accept the terms." />
      <SelectField
        label="Country"
        placeholder="Choose"
        options={options}
        required
        error="Choose one."
      />
    </form>,
  );

  const results = await axe.run(container);
  expect(results.violations.map((violation) => violation.id)).toEqual([]);
});
