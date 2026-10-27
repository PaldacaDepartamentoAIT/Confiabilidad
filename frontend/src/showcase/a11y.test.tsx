import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

const VALID_VALUES = {
  name: "Ana Pérez",
  email: "ana@planta.com",
  password: "s3cret",
  newPassword: "turbina-compresor-7",
  code: "123456",
};

async function renderFilledApp(language: string) {
  const i18n = createI18n(language);
  render(
    <I18nextProvider i18n={i18n}>
      <App />
    </I18nextProvider>,
  );
  const user = userEvent.setup();
  for (const [name, value] of Object.entries(VALID_VALUES)) {
    const input = document.querySelector(`input[name="${name}"]`);
    if (input) await user.type(input, value);
  }
  return screen.getByRole("button", { name: i18n.t("showcase.submit") });
}

// El envío corre con temporizadores simulados y axe, con los reales: el estado queda congelado.
function submitAndWait(button: HTMLElement, milliseconds: number) {
  vi.useFakeTimers();
  try {
    fireEvent.click(button);
    act(() => vi.advanceTimersByTime(milliseconds));
  } finally {
    vi.useRealTimers();
  }
}

describe.each(["es", "pt-BR", "en"])("in %s, the sample page has no violations", (language) => {
  test("with field errors", async () => {
    const submit = await renderFilledApp(language);
    await userEvent.setup().clear(document.querySelector('input[name="email"]')!);
    fireEvent.click(submit);

    expect(document.querySelector('[aria-invalid="true"]')).not.toBeNull();
    expect(await violationsOf(document.documentElement)).toEqual([]);
  });

  test("while processing", async () => {
    const submit = await renderFilledApp(language);
    submitAndWait(submit, 0);

    expect(submit).toHaveAttribute("aria-disabled", "true");
    expect(await violationsOf(document.documentElement)).toEqual([]);
  });

  test("with the demo information message", async () => {
    const submit = await renderFilledApp(language);
    submitAndWait(submit, 3000);

    expect(document.activeElement).toHaveAttribute("tabindex", "-1");
    expect(await violationsOf(document.documentElement)).toEqual([]);
  });

  test("with the sample general error", async () => {
    const i18n = createI18n(language);
    await renderFilledApp(language);
    fireEvent.click(screen.getByRole("button", { name: i18n.t("showcase.showExampleError") }));

    expect(screen.getByText(i18n.t("validation.tooManyAttempts"))).toBeInTheDocument();
    expect(await violationsOf(document.documentElement)).toEqual([]);
  });
});

test("the audit reports a field without a label", async () => {
  const { container } = render(
    <main>
      <h1>Audit</h1>
      <input type="text" />
    </main>,
  );

  expect(await violationsOf(container)).toEqual([expect.stringMatching(/^label: /)]);
});
