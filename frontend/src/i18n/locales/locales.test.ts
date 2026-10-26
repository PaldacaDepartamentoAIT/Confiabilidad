import { en } from "./en";
import { es } from "./es";
import { ptBR } from "./pt-BR";

type Tree = { [key: string]: string | Tree };

function flatten(tree: Tree, prefix = ""): Map<string, string> {
  const entries = new Map<string, string>();
  for (const [key, value] of Object.entries(tree)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof value === "string") {
      entries.set(path, value);
    } else {
      flatten(value, path).forEach((text, nested) => entries.set(nested, text));
    }
  }
  return entries;
}

function findTranslationProblems(locales: Record<string, Tree>, reference: string): string[] {
  const referenceKeys = [...flatten(locales[reference]).keys()];
  const problems: string[] = [];
  for (const [language, tree] of Object.entries(locales)) {
    const entries = flatten(tree);
    for (const key of referenceKeys) {
      if (!entries.has(key)) problems.push(`${language}: missing ${key}`);
    }
    for (const [key, text] of entries) {
      if (!referenceKeys.includes(key)) problems.push(`${language}: extra ${key}`);
      if (text.trim() === "") problems.push(`${language}: empty ${key}`);
    }
  }
  return problems;
}

test("the three languages have the same keys and no empty texts", () => {
  expect(findTranslationProblems({ en, es, "pt-BR": ptBR }, "en")).toEqual([]);
});

test("the check reports missing, extra and empty texts", () => {
  const problems = findTranslationProblems(
    {
      en: { app: { title: "Title", heading: "Heading" } },
      es: { app: { title: " ", extra: "Extra" } },
    },
    "en",
  );
  expect(problems).toEqual([
    "es: missing app.heading",
    "es: empty app.title",
    "es: extra app.extra",
  ]);
});

test("every language covers the groups used by the components", () => {
  expect(Object.keys(en)).toEqual([
    "app",
    "language",
    "button",
    "field",
    "message",
    "validation",
    "showcase",
  ]);
});
