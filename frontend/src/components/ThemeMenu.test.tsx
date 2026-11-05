import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { THEME_STORAGE_KEY, type ThemeStorage } from "../theme/theme";
import { ThemeMenu } from "./ThemeMenu";

function memoryStorage(initial: Record<string, string> = {}): ThemeStorage {
  const values = new Map(Object.entries(initial));
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  };
}

function systemPrefers(dark: boolean) {
  window.matchMedia = vi.fn().mockReturnValue({
    matches: dark,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }) as unknown as typeof window.matchMedia;
}

function renderMenu(storage: ThemeStorage) {
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <ThemeMenu storage={storage} />
      <label>
        Nota
        <input />
      </label>
    </I18nextProvider>,
  );
}

function icon(button: HTMLElement) {
  return button.querySelector("svg")?.getAttribute("data-icon");
}

afterEach(() => {
  document.documentElement.removeAttribute("data-theme");
});

test("with the system in light, the button shows the sun and names the theme", () => {
  systemPrefers(false);
  renderMenu(memoryStorage());

  const button = screen.getByRole("button", { name: "Tema: Claro" });
  expect(icon(button)).toBe("sun");
  expect(button.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
});

test("with the system in dark, the button shows the moon", () => {
  systemPrefers(true);
  renderMenu(memoryStorage());

  expect(icon(screen.getByRole("button", { name: "Tema: Oscuro" }))).toBe("moon");
});

test("offers light and dark with the theme in use checked", async () => {
  const user = userEvent.setup();
  systemPrefers(false);
  renderMenu(memoryStorage({ [THEME_STORAGE_KEY]: "dark" }));

  await user.click(screen.getByRole("button", { name: "Tema: Oscuro" }));

  expect(screen.getByRole("menu", { name: "Tema" })).toBeInTheDocument();
  const items = screen.getAllByRole("menuitemradio");
  expect(items.map((item) => item.textContent)).toEqual(["Claro", "Oscuro"]);
  expect(items.map((item) => item.getAttribute("aria-checked"))).toEqual(["false", "true"]);
});

test("choosing applies and stores the theme, keeping the focus and what was typed", async () => {
  const user = userEvent.setup();
  systemPrefers(false);
  const storage = memoryStorage();
  renderMenu(storage);
  await user.type(screen.getByRole("textbox", { name: "Nota" }), "hola");
  await user.click(screen.getByRole("button", { name: "Tema: Claro" }));

  await user.keyboard("{ArrowDown}{Enter}");

  const button = screen.getByRole("button", { name: "Tema: Oscuro" });
  expect(icon(button)).toBe("moon");
  expect(button).toHaveFocus();
  expect(document.documentElement).toHaveAttribute("data-theme", "dark");
  expect(storage.getItem(THEME_STORAGE_KEY)).toBe("dark");
  expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  expect(screen.getByRole("textbox", { name: "Nota" })).toHaveValue("hola");
});
