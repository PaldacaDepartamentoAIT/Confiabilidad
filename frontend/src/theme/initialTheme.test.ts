import html from "../../index.html?raw";
import { THEME_STORAGE_KEY } from "./theme";

// El script en línea de index.html aplica el tema guardado antes de que cargue la aplicación (D-04).
function inlineScript(): string {
  const match = html.match(/<script>([\s\S]*?)<\/script>/);
  expect(match).not.toBeNull();
  return match?.[1] ?? "";
}

function run(storage: Pick<Storage, "getItem">) {
  // El script usa `localStorage` global; aquí se le pasa uno simulado con el mismo nombre.
  new Function("localStorage", inlineScript())(storage);
}

function storing(value: string | null): Pick<Storage, "getItem"> {
  return { getItem: (key) => (key === THEME_STORAGE_KEY ? value : null) };
}

afterEach(() => {
  document.documentElement.removeAttribute("data-theme");
});

test.each(["light", "dark"])("applies the stored %s theme", (theme) => {
  run(storing(theme));

  expect(document.documentElement).toHaveAttribute("data-theme", theme);
});

test.each([null, "sepia"])("applies nothing when the stored value is %s", (value) => {
  run(storing(value));

  expect(document.documentElement).not.toHaveAttribute("data-theme");
});

test("does not fail when the storage is blocked", () => {
  const blocked = {
    getItem: () => {
      throw new DOMException("blocked", "SecurityError");
    },
  };

  expect(() => run(blocked)).not.toThrow();
  expect(document.documentElement).not.toHaveAttribute("data-theme");
});

test("runs in the head, before the application module, with the same storage key", () => {
  const script = inlineScript();

  expect(script).toContain(`"${THEME_STORAGE_KEY}"`);
  expect(html.indexOf("<script>")).toBeLessThan(html.indexOf("</head>"));
  expect(html.indexOf("<script>")).toBeLessThan(html.indexOf('<script type="module"'));
});
