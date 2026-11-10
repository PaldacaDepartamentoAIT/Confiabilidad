import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";

import { SearchBox } from "./SearchBox";

test("is a search field with a magnifier, named and with a placeholder", () => {
  const { container } = render(<SearchBox label="Buscar en la pantalla" placeholder="Buscar…" />);

  const input = screen.getByRole("searchbox", { name: "Buscar en la pantalla" });
  expect(input).toHaveAttribute("type", "search");
  expect(input).toHaveAttribute("placeholder", "Buscar…");
  expect(input).toHaveAttribute("data-ui", "search");
  expect(input).toHaveClass("field");
  expect(input).toHaveAttribute("autocomplete", "off");
  expect(container.firstElementChild).toHaveClass("search");
  const magnifier = container.querySelector("svg");
  expect(magnifier).toHaveClass("lucide-search");
  expect(magnifier).toHaveAttribute("aria-hidden", "true");
  expect(container.firstElementChild?.firstElementChild).toBe(magnifier);
});

test("is only visual: typing works but nothing is searched or reported", async () => {
  const user = userEvent.setup();
  const submit = vi.fn((event: Event) => event.preventDefault());
  document.addEventListener("submit", submit);
  render(<SearchBox label="Buscar" placeholder="Buscar…" />);
  const input = screen.getByRole("searchbox");

  await user.type(input, "bomba{Enter}");

  expect(input).toHaveValue("bomba");
  expect(submit).not.toHaveBeenCalled();
  document.removeEventListener("submit", submit);
});

test("has no accessibility violations", async () => {
  const { container } = render(<SearchBox label="Buscar" placeholder="Buscar…" />);
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});

describe("en pantallas de menos de 560 px", () => {
  type Listener = (event: { matches: boolean }) => void;

  function stubScreen(narrow: boolean) {
    const listeners = new Set<Listener>();
    vi.stubGlobal("matchMedia", (query: string) => ({
      matches: query === "(max-width: 559px)" ? narrow : false,
      addEventListener: (_type: string, listener: Listener) => {
        if (query === "(max-width: 559px)") listeners.add(listener);
      },
      removeEventListener: (_type: string, listener: Listener) => listeners.delete(listener),
    }));
    return { resize: (matches: boolean) => listeners.forEach((listener) => listener({ matches })) };
  }

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("se reduce a un botón con lupa que tiene el nombre del buscador, y el campo queda cerrado", () => {
    stubScreen(true);
    const { container } = render(<SearchBox label="Buscar" placeholder="Buscar…" />);

    const toggle = screen.getByRole("button", { name: "Buscar" });
    expect(toggle).toHaveClass("search-toggle");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(toggle.querySelector("svg")).toHaveClass("lucide-search");
    const field = container.querySelector(".search");
    expect(field).toHaveClass("narrow");
    expect(field).not.toHaveClass("open");
    expect(toggle).toHaveAttribute("aria-controls", field?.id);
  });

  it("el botón puede llamarse de otra forma que el campo", () => {
    stubScreen(true);
    render(<SearchBox label="Buscar" placeholder="Buscar…" openLabel="Abrir el buscador" />);
    expect(screen.getByRole("button", { name: "Abrir el buscador" })).toBeInTheDocument();
  });

  it("pulsarlo despliega el campo, con el foco dentro, y Escape lo cierra devolviendo el foco al botón", async () => {
    stubScreen(true);
    const user = userEvent.setup();
    const { container } = render(<SearchBox label="Buscar" placeholder="Buscar…" />);
    const toggle = screen.getByRole("button", { name: "Buscar" });

    await user.click(toggle);

    expect(container.querySelector(".search")).toHaveClass("open");
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    const input = screen.getByRole("searchbox");
    expect(input).toHaveFocus();

    await user.type(input, "bomba");
    await user.keyboard("{Escape}");

    expect(container.querySelector(".search")).not.toHaveClass("open");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(toggle).toHaveFocus();
  });

  it("Escape no hace nada si el campo está cerrado", async () => {
    stubScreen(true);
    const user = userEvent.setup();
    render(<SearchBox label="Buscar" placeholder="Buscar…" />);

    await user.keyboard("{Escape}");

    expect(screen.getByRole("button", { name: "Buscar" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("en pantalla ancha no hay botón y el campo se ve siempre", () => {
    stubScreen(false);
    const { container } = render(<SearchBox label="Buscar" placeholder="Buscar…" />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(container.querySelector(".search")).not.toHaveClass("narrow");
  });

  it("se cierra si la pantalla se ensancha con el campo abierto", async () => {
    const screenControl = stubScreen(true);
    const user = userEvent.setup();
    const { container } = render(<SearchBox label="Buscar" placeholder="Buscar…" />);
    await user.click(screen.getByRole("button", { name: "Buscar" }));

    act(() => screenControl.resize(false));

    expect(container.querySelector(".search")).not.toHaveClass("open");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("si se ensancha y se vuelve a estrechar, el campo no reaparece abierto", async () => {
    const screenControl = stubScreen(true);
    const user = userEvent.setup();
    const { container } = render(<SearchBox label="Buscar" placeholder="Buscar…" />);
    await user.click(screen.getByRole("button", { name: "Buscar" }));

    act(() => screenControl.resize(false));
    act(() => screenControl.resize(true));

    expect(container.querySelector(".search")).not.toHaveClass("open");
    expect(screen.getByRole("button", { name: "Buscar" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("no tiene violaciones de accesibilidad cerrado ni abierto", async () => {
    stubScreen(true);
    const user = userEvent.setup();
    const { container } = render(<SearchBox label="Buscar" placeholder="Buscar…" />);
    const run = () => axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    expect((await run()).violations).toEqual([]);

    await user.click(screen.getByRole("button", { name: "Buscar" }));
    expect((await run()).violations).toEqual([]);
  });
});
