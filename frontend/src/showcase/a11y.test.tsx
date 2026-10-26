import { render } from "@testing-library/react";
import axe from "axe-core";
import { I18nextProvider } from "react-i18next";

import { App } from "../App";
import { createI18n } from "../i18n";

async function violationsOf(element: Element): Promise<string[]> {
  const results = await axe.run(element);
  return results.violations.map(
    (violation) => `${violation.id}: ${violation.nodes.map((node) => node.target).join(", ")}`,
  );
}

test.each(["es", "pt-BR", "en"])(
  "the sample page has no accessibility violations in %s",
  async (language) => {
    render(
      <I18nextProvider i18n={createI18n(language)}>
        <App />
      </I18nextProvider>,
    );

    expect(await violationsOf(document.documentElement)).toEqual([]);
  },
);

test("the audit reports a field without a label", async () => {
  const { container } = render(
    <main>
      <h1>Audit</h1>
      <input type="text" />
    </main>,
  );

  expect(await violationsOf(container)).toEqual([expect.stringMatching(/^label: /)]);
});
