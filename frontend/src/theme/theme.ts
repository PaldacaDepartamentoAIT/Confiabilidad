export const THEMES = ["light", "dark"] as const;

export type Theme = (typeof THEMES)[number];

export const THEME_STORAGE_KEY = "confiabilidad.theme";

export type ThemeStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

export type ThemeEnvironment = {
  storage?: ThemeStorage;
  root?: HTMLElement;
  prefersDark?: () => boolean;
};

const ANIMATION_CLASS = "theme-anim";
const ANIMATION_MS = 400;

function isTheme(value: string): value is Theme {
  return (THEMES as readonly string[]).includes(value);
}

// Si el navegador bloquea el almacenamiento, se actúa como si no hubiera nada guardado.
function attempt<T>(action: () => T): T | undefined {
  try {
    return action();
  } catch {
    return undefined;
  }
}

function systemPrefersDark(): boolean {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

function rootOf(env: ThemeEnvironment): HTMLElement {
  return env.root ?? document.documentElement;
}

export function getTheme(env: ThemeEnvironment = {}): Theme {
  const fixed = rootOf(env).getAttribute("data-theme");
  if (fixed !== null && isTheme(fixed)) return fixed;
  return (env.prefersDark ?? systemPrefersDark)() ? "dark" : "light";
}

export function initTheme(env: ThemeEnvironment = {}): Theme {
  const stored = env.storage
    ? (attempt(() => env.storage?.getItem(THEME_STORAGE_KEY)) ?? null)
    : null;
  if (stored !== null) {
    if (isTheme(stored)) {
      rootOf(env).setAttribute("data-theme", stored);
    } else {
      attempt(() => env.storage?.removeItem(THEME_STORAGE_KEY));
    }
  }
  return getTheme(env);
}

const timers = new WeakMap<HTMLElement, ReturnType<typeof setTimeout>>();

export function toggleTheme(env: ThemeEnvironment = {}): Theme {
  const root = rootOf(env);
  const next: Theme = getTheme(env) === "dark" ? "light" : "dark";
  const running = timers.get(root);
  if (running !== undefined) clearTimeout(running);
  root.classList.add(ANIMATION_CLASS);
  root.setAttribute("data-theme", next);
  timers.set(
    root,
    setTimeout(() => {
      root.classList.remove(ANIMATION_CLASS);
      timers.delete(root);
    }, ANIMATION_MS),
  );
  attempt(() => env.storage?.setItem(THEME_STORAGE_KEY, next));
  return next;
}
