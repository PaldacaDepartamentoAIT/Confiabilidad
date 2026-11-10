import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { createRef } from "react";

import { Checkbox } from "./Checkbox";
import { CustomSelect } from "./CustomSelect";
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

  // jsdom no tiene canvas: axe no puede medir el contraste, así que se excluye de forma explícita.
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations.map((violation) => violation.id)).toEqual([]);
});

describe("selector propio", () => {
  const countries = [
    { value: "BR", label: "Brazil" },
    { value: "CL", label: "Chile" },
    { value: "CO", label: "Colombia" },
  ];

  it("se nombra por su etiqueta, marca el obligatorio y muestra el texto de reserva sin valor", () => {
    render(
      <CustomSelect label="Country" placeholder="Choose" options={countries} required name="c" />,
    );

    const trigger = screen.getByRole("combobox", { name: "Country" });
    expect(trigger.tagName).toBe("BUTTON");
    expect(trigger).toHaveAttribute("name", "c");
    expect(trigger).toHaveAttribute("value", "");
    expect(trigger).toHaveAttribute("aria-required", "true");
    expect(trigger).toHaveTextContent("Choose");
    expect(trigger.querySelector(".value")).toHaveClass("placeholder");
    expect(screen.getByText("*").closest("label")).not.toBeNull();
    expect(trigger).toHaveClass("field", "select-trigger");
    expect(trigger).toHaveAttribute("data-ui", "field");
    expect(trigger.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  });

  it("al elegir una opción muestra su texto, guarda su valor y avisa del cambio", async () => {
    const user = userEvent.setup();
    const onValueChange = vi.fn();
    render(
      <CustomSelect
        label="Country"
        placeholder="Choose"
        options={countries}
        onValueChange={onValueChange}
      />,
    );
    const trigger = screen.getByRole("combobox", { name: "Country" });

    await user.click(trigger);
    expect(screen.getAllByRole("option").map((option) => option.textContent)).toEqual([
      "Brazil",
      "Chile",
      "Colombia",
    ]);
    await user.click(screen.getByRole("option", { name: "Chile" }));

    expect(trigger).toHaveTextContent("Chile");
    expect(trigger).toHaveAttribute("value", "CL");
    expect(trigger.querySelector(".value")).not.toHaveClass("placeholder");
    expect(onValueChange).toHaveBeenCalledWith("CL");
    expect(trigger).toHaveFocus();
  });

  it("se maneja con el teclado y escribir salta a una opción", async () => {
    const user = userEvent.setup();
    render(<CustomSelect label="Country" placeholder="Choose" options={countries} />);
    const trigger = screen.getByRole("combobox", { name: "Country" });

    await user.tab();
    await user.keyboard("co{Enter}");

    expect(trigger).toHaveTextContent("Colombia");
    expect(trigger).toHaveAttribute("value", "CO");
  });

  it("acepta un valor inicial y también un valor controlado", () => {
    const { rerender } = render(
      <CustomSelect label="Country" placeholder="Choose" options={countries} defaultValue="CL" />,
    );
    expect(screen.getByRole("combobox")).toHaveTextContent("Chile");

    rerender(<CustomSelect label="Country" placeholder="Choose" options={countries} value="CO" />);
    expect(screen.getByRole("combobox")).toHaveTextContent("Colombia");
    expect(screen.getByRole("combobox")).toHaveAttribute("value", "CO");
  });

  it("enlaza la ayuda y el error, se marca como inválido y los quita al desaparecer", () => {
    const { rerender } = render(
      <CustomSelect
        label="Country"
        placeholder="Choose"
        options={countries}
        hint="Where you live."
        error="Choose one."
      />,
    );
    const trigger = screen.getByRole("combobox", { name: "Country" });
    expect(trigger).toHaveAttribute("aria-invalid", "true");
    expect(trigger).toHaveAccessibleDescription("Where you live. Choose one.");
    expect(screen.getByText("Where you live.")).toHaveClass("help");
    expect(screen.getByText("Choose one.").closest("p")).toHaveClass("error-msg");

    rerender(<CustomSelect label="Country" placeholder="Choose" options={countries} />);

    expect(trigger).not.toHaveAttribute("aria-invalid");
    expect(trigger).not.toHaveAttribute("aria-describedby");
    expect(trigger).not.toHaveAttribute("aria-required");
  });

  it("pasa su ref al botón y avisa cuando el foco sale", async () => {
    const user = userEvent.setup();
    const ref = createRef<HTMLButtonElement>();
    const onBlur = vi.fn();
    render(
      <>
        <CustomSelect
          ref={ref}
          label="Country"
          placeholder="Choose"
          options={countries}
          onBlur={onBlur}
        />
        <button type="button">next</button>
      </>,
    );

    expect(ref.current).toBe(screen.getByRole("combobox", { name: "Country" }));
    await user.tab();
    await user.tab();

    expect(onBlur).toHaveBeenCalledTimes(1);
  });

  it("axe no encuentra fallos con error, cerrado ni abierto", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <form>
        <CustomSelect
          label="Country"
          placeholder="Choose"
          options={countries}
          required
          error="Choose one."
        />
      </form>,
    );
    const run = () => axe.run(container, { rules: { "color-contrast": { enabled: false } } });

    expect((await run()).violations.map((violation) => violation.id)).toEqual([]);
    await user.click(screen.getByRole("combobox"));
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 30));
    });
    expect((await run()).violations.map((violation) => violation.id)).toEqual([]);
  });
});
