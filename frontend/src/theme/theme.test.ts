import {
  THEME_STORAGE_KEY,
  getTheme,
  initTheme,
  toggleTheme,
  type ThemeEnvironment,
  type ThemeStorage,
} from "./theme";

function memoryStorage(initial?: string): ThemeStorage & { values: Map<string, string> } {
  const values = new Map<string, string>();
  if (initial !== undefined) values.set(THEME_STORAGE_KEY, initial);
  return {
    values,
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  };
}

function environment(
  overrides: Partial<ThemeEnvironment> & { storage?: ThemeStorage } = {},
): ThemeEnvironment & { root: HTMLElement } {
  const root = document.createElement("html");
  return { root, prefersDark: () => false, ...overrides };
}

afterEach(() => {
  vi.useRealTimers();
});

describe("initial theme (RF-001)", () => {
  test("follows the operating system when nothing is saved", () => {
    const light = environment({ storage: memoryStorage() });
    expect(initTheme(light)).toBe("light");
    expect(light.root).not.toHaveAttribute("data-theme");

    const dark = environment({ storage: memoryStorage(), prefersDark: () => true });
    expect(initTheme(dark)).toBe("dark");
    expect(dark.root).not.toHaveAttribute("data-theme");
  });

  test("works without storage", () => {
    expect(initTheme(environment({ prefersDark: () => true }))).toBe("dark");
  });

  test.each(["light", "dark"] as const)("a saved %s theme wins over the system", (saved) => {
    const env = environment({
      storage: memoryStorage(saved),
      prefersDark: () => saved === "light",
    });
    expect(initTheme(env)).toBe(saved);
    expect(env.root).toHaveAttribute("data-theme", saved);
  });
});

describe("invalid saved theme (RF-003)", () => {
  test.each(["", "blue", "DARK", "system", "undefined"])(
    "ignores %j, deletes it and follows the system",
    (invalid) => {
      const storage = memoryStorage(invalid);
      const env = environment({ storage, prefersDark: () => true });
      expect(initTheme(env)).toBe("dark");
      expect(env.root).not.toHaveAttribute("data-theme");
      expect(storage.values.has(THEME_STORAGE_KEY)).toBe(false);
    },
  );

  test("acts as if nothing were saved when the storage throws", () => {
    const broken: ThemeStorage = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      },
      removeItem: () => {
        throw new Error("blocked");
      },
    };
    const env = environment({ storage: broken, prefersDark: () => true });
    expect(initTheme(env)).toBe("dark");
    expect(() => toggleTheme(env)).not.toThrow();
    expect(env.root).toHaveAttribute("data-theme", "light");
  });
});

describe("toggle (RF-002)", () => {
  test("switches from the system theme to the opposite one and saves it", () => {
    const storage = memoryStorage();
    const env = environment({ storage, prefersDark: () => true });
    initTheme(env);
    expect(toggleTheme(env)).toBe("light");
    expect(env.root).toHaveAttribute("data-theme", "light");
    expect(storage.values.get(THEME_STORAGE_KEY)).toBe("light");
    expect(getTheme(env)).toBe("light");
  });

  test("alternates between light and dark on each call", () => {
    const env = environment({ storage: memoryStorage("light") });
    initTheme(env);
    expect(toggleTheme(env)).toBe("dark");
    expect(toggleTheme(env)).toBe("light");
    expect(getTheme(env)).toBe("light");
  });

  test("marks the root as changing theme for 0.4 s and then clears the mark", () => {
    vi.useFakeTimers();
    const env = environment({ storage: memoryStorage("light") });
    toggleTheme(env);
    expect(env.root).toHaveClass("theme-anim");
    vi.advanceTimersByTime(399);
    expect(env.root).toHaveClass("theme-anim");
    vi.advanceTimersByTime(1);
    expect(env.root).not.toHaveClass("theme-anim");
  });

  test("a second toggle restarts the 0.4 s window", () => {
    vi.useFakeTimers();
    const env = environment({ storage: memoryStorage("light") });
    toggleTheme(env);
    vi.advanceTimersByTime(300);
    toggleTheme(env);
    vi.advanceTimersByTime(300);
    expect(env.root).toHaveClass("theme-anim");
    vi.advanceTimersByTime(100);
    expect(env.root).not.toHaveClass("theme-anim");
  });
});

describe("current theme", () => {
  test("reads the fixed theme, otherwise the system one", () => {
    const env = environment({ prefersDark: () => true });
    expect(getTheme(env)).toBe("dark");
    env.root.setAttribute("data-theme", "light");
    expect(getTheme(env)).toBe("light");
  });

  test("uses the browser media query by default", () => {
    const matchMedia = vi.fn().mockReturnValue({ matches: true });
    vi.stubGlobal("matchMedia", matchMedia);
    const root = document.createElement("html");
    expect(getTheme({ root })).toBe("dark");
    expect(matchMedia).toHaveBeenCalledWith("(prefers-color-scheme: dark)");
    vi.unstubAllGlobals();
  });

  test("assumes light when the browser has no media queries", () => {
    vi.stubGlobal("matchMedia", undefined);
    expect(getTheme({ root: document.createElement("html") })).toBe("light");
    vi.unstubAllGlobals();
  });
});
