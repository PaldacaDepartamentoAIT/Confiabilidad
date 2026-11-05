import { useCallback, useState, useSyncExternalStore } from "react";

export const THEMES = ["light", "dark"] as const;

export type Theme = (typeof THEMES)[number];

// El script de index.html lee esta misma clave antes del primer pintado (D-04).
export const THEME_STORAGE_KEY = "confiabilidad.theme";

export type ThemeStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

const DARK_QUERY = "(prefers-color-scheme: dark)";

// Si el navegador bloquea el almacenamiento, se actúa como si no hubiera nada guardado.
function attempt<T>(action: () => T): T | undefined {
  try {
    return action();
  } catch {
    return undefined;
  }
}

function isTheme(value: string): value is Theme {
  return (THEMES as readonly string[]).includes(value);
}

export function readStoredTheme(storage: ThemeStorage | undefined): Theme | null {
  if (!storage) return null;
  const stored = attempt(() => storage.getItem(THEME_STORAGE_KEY)) ?? null;
  if (stored === null) return null;
  if (isTheme(stored)) return stored;
  attempt(() => storage.removeItem(THEME_STORAGE_KEY));
  return null;
}

// Sin elección no hay `data-theme` y manda `prefers-color-scheme` (D-13).
export function applyTheme(theme: Theme | null): void {
  if (theme) document.documentElement.setAttribute("data-theme", theme);
  else document.documentElement.removeAttribute("data-theme");
}

function darkQuery(): MediaQueryList | undefined {
  return typeof window.matchMedia === "function" ? window.matchMedia(DARK_QUERY) : undefined;
}

function subscribeToSystem(onChange: () => void): () => void {
  const query = darkQuery();
  query?.addEventListener("change", onChange);
  return () => query?.removeEventListener("change", onChange);
}

function systemTheme(): Theme {
  return darkQuery()?.matches ? "dark" : "light";
}

export function useTheme(storage: ThemeStorage | undefined) {
  const [chosen, setChosen] = useState(() => readStoredTheme(storage));
  const system = useSyncExternalStore(subscribeToSystem, systemTheme);

  const choose = useCallback(
    (theme: Theme) => {
      if (storage) attempt(() => storage.setItem(THEME_STORAGE_KEY, theme));
      applyTheme(theme);
      setChosen(theme);
    },
    [storage],
  );

  return { theme: chosen ?? system, choose };
}
