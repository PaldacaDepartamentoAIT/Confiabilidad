import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { I18nextProvider } from "react-i18next";

import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { createI18n } from "../i18n";
import { ThemeButton } from "./ThemeButton";
import { THEME_STORAGE_KEY, type ThemeStorage } from "./theme";

function memoryStorage(): ThemeStorage & { values: Map<string, string> } {
  const values = new Map<string, string>();
  return {
    values,
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  };
}

function renderButton(language = "es", storage?: ThemeStorage) {
  return render(
    <I18nextProvider i18n={createI18n(language)}>
      <LiveAnnouncer>
        <ThemeButton storage={storage} />
      </LiveAnnouncer>
    </I18nextProvider>,
  );
}

function mockSystemTheme(dark: boolean) {
  vi.stubGlobal("matchMedia", () => ({ matches: dark }));
}

afterEach(() => {
  document.documentElement.removeAttribute("data-theme");
  document.documentElement.classList.remove("theme-anim");
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

test("shows the system theme as its label and names the action in its accessible name", () => {
  mockSystemTheme(false);
  renderButton("es");

  const button = screen.getByRole("button", { name: "Tema claro. Cambiar tema" });
  expect(button).toHaveTextContent("Claro");
  expect(button).toHaveAttribute("data-ui", "sidebar-button");
  expect(button).toHaveAttribute("type", "button");
});

test("shows the dark label when the system is dark", () => {
  mockSystemTheme(true);
  renderButton("en");
  expect(screen.getByRole("button", { name: "Dark theme. Switch theme" })).toHaveTextContent(
    "Dark",
  );
});

test("a click switches the theme, saves it and updates label, name and icon", async () => {
  mockSystemTheme(false);
  const storage = memoryStorage();
  const user = userEvent.setup();
  renderButton("es", storage);
  const sun = document.querySelector("svg[data-icon='sun']");
  expect(sun).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Tema claro. Cambiar tema" }));

  expect(document.documentElement).toHaveAttribute("data-theme", "dark");
  expect(storage.values.get(THEME_STORAGE_KEY)).toBe("dark");
  const button = screen.getByRole("button", { name: "Tema oscuro. Cambiar tema" });
  expect(button).toHaveTextContent("Oscuro");
  expect(document.querySelector("svg[data-icon='moon']")).toBeInTheDocument();
  expect(document.querySelector("svg[data-icon='sun']")).not.toBeInTheDocument();

  await user.click(button);
  expect(document.documentElement).toHaveAttribute("data-theme", "light");
  expect(screen.getByRole("button", { name: "Tema claro. Cambiar tema" })).toBeInTheDocument();
});

test("tells the screen reader the new theme", async () => {
  mockSystemTheme(false);
  const user = userEvent.setup();
  renderButton("es");

  await user.click(screen.getByRole("button"));
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 5));
  });

  expect(screen.getByRole("status")).toHaveTextContent("Tema oscuro");
});

test("works with the keyboard", async () => {
  mockSystemTheme(false);
  const user = userEvent.setup();
  renderButton("pt-BR");

  await user.tab();
  expect(screen.getByRole("button")).toHaveFocus();
  await user.keyboard("{Enter}");
  expect(document.documentElement).toHaveAttribute("data-theme", "dark");
  await user.keyboard(" ");
  expect(document.documentElement).toHaveAttribute("data-theme", "light");
});

test("has no accessibility violations in either theme", async () => {
  mockSystemTheme(false);
  const user = userEvent.setup();
  const { container } = renderButton("es");
  const run = () => axe.run(container, { rules: { "color-contrast": { enabled: false } } });

  expect((await run()).violations).toEqual([]);
  await user.click(screen.getByRole("button"));
  expect((await run()).violations).toEqual([]);
});
