import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { createRef } from "react";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../../i18n";

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

it.each([
  ["casilla", (error?: string) => <Checkbox label="I accept" error={error} />],
  [
    "selector",
    (error?: string) => (
      <SelectField label="Country" placeholder="Choose" options={options} error={error} />
    ),
  ],
])("%s reserva el hueco del error con y sin error", (_, field) => {
  const { container, rerender } = render(field());

  const slot = container.querySelector(".field__error-slot");
  expect(slot).toBeEmptyDOMElement();

  rerender(field("Required."));

  expect(container.querySelector(".field__error-slot")).toBe(slot);
  expect(slot).toHaveTextContent("Required.");
});

const COUNTRIES = [
  { value: "BR", label: "Brazil" },
  { value: "CL", label: "Chile" },
  { value: "EC", label: "Ecuador" },
  { value: "ES", label: "España" },
  { value: "PE", label: "Perú" },
];

function renderSelect(props: Partial<Parameters<typeof SelectField>[0]> = {}) {
  const onBlur = vi.fn();
  const { container } = render(
    <form>
      <SelectField
        label="Country"
        placeholder="Choose"
        options={COUNTRIES}
        name="country"
        onBlur={onBlur}
        {...props}
      />
      <button type="button">Next</button>
    </form>,
  );
  return {
    onBlur,
    container,
    control: screen.getByRole("combobox", { name: "Country" }),
  };
}

const highlighted = (control: HTMLElement) =>
  document.getElementById(control.getAttribute("aria-activedescendant") ?? "")?.textContent;

describe("selector", () => {
  it("is a button combobox with a name and a value, closed and without a native select", () => {
    const { control } = renderSelect({ required: true });

    expect(control.tagName).toBe("BUTTON");
    expect(control).toHaveAttribute("type", "button");
    expect(control).toHaveAttribute("name", "country");
    expect(control).toHaveValue("");
    expect(control).toHaveTextContent("Choose");
    expect(control).toHaveAttribute("aria-required", "true");
    expect(control).toHaveAttribute("aria-expanded", "false");
    expect(control).not.toHaveAttribute("aria-activedescendant");
    expect(control.querySelector("svg")).toHaveAttribute("data-icon", "chevron-down");
    expect(document.querySelector("select")).toBeNull();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(screen.getByText("*").closest("label")).not.toBeNull();
  });

  it.each(["{Enter}", " ", "{ArrowDown}", "{Alt>}{ArrowDown}{/Alt}"])(
    "%s opens the list with the chosen option highlighted",
    async (key) => {
      const user = userEvent.setup();
      const { control } = renderSelect({ defaultValue: "EC" });
      control.focus();

      await user.keyboard(key);

      const list = screen.getByRole("listbox", { name: "Country" });
      expect(control).toHaveAttribute("aria-expanded", "true");
      expect(control).toHaveAttribute("aria-controls", list.id);
      expect(screen.getAllByRole("option").map((option) => option.textContent)).toEqual(
        COUNTRIES.map((country) => country.label),
      );
      expect(screen.getByRole("option", { name: "Ecuador" })).toHaveAttribute(
        "aria-selected",
        "true",
      );
      expect(highlighted(control)).toBe("Ecuador");
      expect(control).toHaveFocus();
    },
  );

  it("arrows, Home, End and the page keys move the highlight without choosing", async () => {
    const user = userEvent.setup();
    const { control } = renderSelect();
    await user.click(control);
    expect(highlighted(control)).toBe("Brazil");

    await user.keyboard("{ArrowDown}");
    expect(highlighted(control)).toBe("Chile");
    await user.keyboard("{ArrowUp}{ArrowUp}");
    expect(highlighted(control)).toBe("Brazil");
    await user.keyboard("{End}");
    expect(highlighted(control)).toBe("Perú");
    await user.keyboard("{ArrowDown}");
    expect(highlighted(control)).toBe("Perú");
    await user.keyboard("{Home}");
    expect(highlighted(control)).toBe("Brazil");
    await user.keyboard("{PageDown}");
    expect(highlighted(control)).toBe("Perú");
    await user.keyboard("{PageUp}");
    expect(highlighted(control)).toBe("Brazil");
    expect(control).toHaveValue("");
  });

  it("typing jumps to the option that starts with the letters, without accents", async () => {
    const user = userEvent.setup();
    const { control } = renderSelect();
    control.focus();

    await user.keyboard("pe");

    expect(control).toHaveAttribute("aria-expanded", "true");
    expect(highlighted(control)).toBe("Perú");
  });

  it("Enter chooses the highlighted option and closes, keeping the focus", async () => {
    const user = userEvent.setup();
    const { control } = renderSelect();
    await user.click(control);

    await user.keyboard("{ArrowDown}{Enter}");

    expect(control).toHaveValue("CL");
    expect(control).toHaveTextContent("Chile");
    expect(control).toHaveAttribute("aria-expanded", "false");
    expect(control).toHaveFocus();
  });

  it("Escape closes without changing the value", async () => {
    const user = userEvent.setup();
    const { control } = renderSelect({ defaultValue: "ES" });
    await user.click(control);

    await user.keyboard("{ArrowDown}{Escape}");

    expect(control).toHaveValue("ES");
    expect(control).toHaveAttribute("aria-expanded", "false");
    expect(control).toHaveFocus();
  });

  it("Tab chooses the highlighted option and leaves", async () => {
    const user = userEvent.setup();
    const { control, onBlur } = renderSelect();
    await user.click(control);

    await user.keyboard("{ArrowDown}");
    await user.tab();

    expect(control).toHaveValue("CL");
    expect(screen.getByRole("button", { name: "Next" })).toHaveFocus();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(onBlur).toHaveBeenCalled();
  });

  it("a click on an option chooses it without taking the focus away", async () => {
    const user = userEvent.setup();
    const { control, onBlur } = renderSelect();
    await user.click(control);

    await user.click(screen.getByRole("option", { name: "España" }));

    expect(control).toHaveValue("ES");
    expect(control).toHaveFocus();
    expect(onBlur).not.toHaveBeenCalled();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("a click outside closes the list without choosing", async () => {
    const user = userEvent.setup();
    const { control, onBlur } = renderSelect({ defaultValue: "ES" });
    await user.click(control);
    await user.keyboard("{ArrowDown}");

    await user.click(document.body);

    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(control).toHaveValue("ES");
    expect(onBlur).toHaveBeenCalled();
  });

  it("a second click on the control closes the list", async () => {
    const user = userEvent.setup();
    const { control } = renderSelect();
    await user.click(control);

    await user.click(control);

    expect(control).toHaveAttribute("aria-expanded", "false");
  });

  it("links the hint and the error and is marked invalid", () => {
    const { control } = renderSelect({ hint: "Where you live.", error: "Choose one." });

    expect(control).toHaveAttribute("aria-invalid", "true");
    expect(control).toHaveAccessibleDescription("Where you live. Choose one.");
  });

  it("forwards its ref to the control", () => {
    const ref = createRef<HTMLButtonElement>();
    render(<SelectField ref={ref} label="Country" placeholder="Choose" options={COUNTRIES} />);

    expect(ref.current).toBe(screen.getByRole("combobox", { name: "Country" }));
  });

  it("axe finds nothing with the list open", async () => {
    const user = userEvent.setup();
    const { control, container } = renderSelect({ required: true, error: "Choose one." });
    await user.click(control);

    const results = await axe.run(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations.map((violation) => violation.id)).toEqual([]);
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

it("el selector lleva su «?» y lee su descripción", () => {
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <SelectField label="País" placeholder="Elige" options={options} help="Donde resides." />
    </I18nextProvider>,
  );

  expect(screen.getByRole("button", { name: "Ayuda (País)" })).toBeInTheDocument();
  expect(screen.getByRole("combobox", { name: "País" })).toHaveAccessibleDescription(
    "Donde resides.",
  );
});

// Nunca se ejecuta: solo comprueba en compilación que la casilla no admite «?» (RF-014).
export function checkboxHasNoHelp() {
  // @ts-expect-error: the checkbox has no help
  return <Checkbox label="I accept" help="x" />;
}
