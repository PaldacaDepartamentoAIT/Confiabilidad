import { act, renderHook } from "@testing-library/react";

import {
  THEME_STORAGE_KEY,
  applyTheme,
  readStoredTheme,
  useTheme,
  type ThemeStorage,
} from "./theme";

function memoryStorage(initial: Record<string, string> = {}): ThemeStorage {
  const values = new Map(Object.entries(initial));
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  };
}

function blockedStorage(): ThemeStorage {
  const fail = () => {
    throw new DOMException("blocked", "SecurityError");
  };
  return { getItem: fail, setItem: fail, removeItem: fail };
}

// jsdom no trae `matchMedia`: se simula el tema del sistema y su cambio.
function systemPrefers(dark: boolean) {
  const listeners = new Set<() => void>();
  const query = {
    matches: dark,
    addEventListener: (_: string, listener: () => void) => listeners.add(listener),
    removeEventListener: (_: string, listener: () => void) => listeners.delete(listener),
  };
  window.matchMedia = vi.fn().mockReturnValue(query) as unknown as typeof window.matchMedia;
  return {
    change(next: boolean) {
      query.matches = next;
      listeners.forEach((listener) => listener());
    },
  };
}

afterEach(() => {
  document.documentElement.removeAttribute("data-theme");
});

describe("tema guardado", () => {
  it.each(["light", "dark"] as const)("reads %s", (theme) => {
    expect(readStoredTheme(memoryStorage({ [THEME_STORAGE_KEY]: theme }))).toBe(theme);
  });

  it("is null when nothing was chosen or without storage", () => {
    expect(readStoredTheme(memoryStorage())).toBeNull();
    expect(readStoredTheme(undefined)).toBeNull();
  });

  it("ignores and deletes an invalid value", () => {
    const storage = memoryStorage({ [THEME_STORAGE_KEY]: "sepia" });

    expect(readStoredTheme(storage)).toBeNull();
    expect(storage.getItem(THEME_STORAGE_KEY)).toBeNull();
  });

  it("acts as if nothing was stored when the storage is blocked", () => {
    expect(readStoredTheme(blockedStorage())).toBeNull();
  });
});

describe("aplicar el tema", () => {
  it("sets and removes data-theme on the root element", () => {
    applyTheme("dark");
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");

    applyTheme(null);
    expect(document.documentElement).not.toHaveAttribute("data-theme");
  });
});

describe("useTheme", () => {
  it("without a choice, uses the system theme and follows its changes", () => {
    const system = systemPrefers(true);
    const { result } = renderHook(() => useTheme(memoryStorage()));

    expect(result.current.theme).toBe("dark");
    expect(document.documentElement).not.toHaveAttribute("data-theme");

    act(() => system.change(false));

    expect(result.current.theme).toBe("light");
  });

  it("uses the stored choice over the system theme", () => {
    systemPrefers(true);
    const { result } = renderHook(() => useTheme(memoryStorage({ [THEME_STORAGE_KEY]: "light" })));

    expect(result.current.theme).toBe("light");
  });

  it("choosing stores the theme, applies it and stops following the system", () => {
    const system = systemPrefers(false);
    const storage = memoryStorage();
    const { result } = renderHook(() => useTheme(storage));

    act(() => result.current.choose("dark"));

    expect(result.current.theme).toBe("dark");
    expect(storage.getItem(THEME_STORAGE_KEY)).toBe("dark");
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");

    act(() => system.change(false));

    expect(result.current.theme).toBe("dark");
  });

  it("choosing works with the storage blocked", () => {
    systemPrefers(false);
    const { result } = renderHook(() => useTheme(blockedStorage()));

    act(() => result.current.choose("dark"));

    expect(result.current.theme).toBe("dark");
    expect(document.documentElement).toHaveAttribute("data-theme", "dark");
  });

  it("without matchMedia, the system theme is light", () => {
    // @ts-expect-error: simula un entorno sin matchMedia
    delete window.matchMedia;
    const { result } = renderHook(() => useTheme(undefined));

    expect(result.current.theme).toBe("light");
  });
});
