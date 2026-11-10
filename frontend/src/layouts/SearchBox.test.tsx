import { render, screen } from "@testing-library/react";
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
