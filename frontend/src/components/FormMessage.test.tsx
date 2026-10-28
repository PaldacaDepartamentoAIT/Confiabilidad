import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { FormMessage } from "./FormMessage";

test.each([
  ["error", "Error: Demasiados intentos. Espera unos minutos y vuelve a intentarlo."],
  ["success", "Éxito: Demasiados intentos. Espera unos minutos y vuelve a intentarlo."],
  ["info", "Información: Demasiados intentos. Espera unos minutos y vuelve a intentarlo."],
] as const)("a %s message starts with its translated prefix", (type, text) => {
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <FormMessage type={type} messageKey="validation.tooManyAttempts" />
    </I18nextProvider>,
  );

  expect(
    screen.getByText("Demasiados intentos", { exact: false }).closest("div"),
  ).toHaveTextContent(text);
});

test("translates the message when the language changes", async () => {
  const i18n = createI18n("es");
  render(
    <I18nextProvider i18n={i18n}>
      <FormMessage type="info" messageKey="showcase.demoInfo" />
    </I18nextProvider>,
  );

  await act(() => i18n.changeLanguage("pt-BR"));

  expect(
    screen.getByText("Formulário de demonstração", { exact: false }).closest("div"),
  ).toHaveTextContent("Informação: Formulário de demonstração: nenhum dado é enviado.");
});

test("can receive the focus from code but is not in the tab order", async () => {
  const user = userEvent.setup();
  const ref = createRef<HTMLDivElement>();
  render(
    <I18nextProvider i18n={createI18n("en")}>
      <button type="button">Before</button>
      <FormMessage ref={ref} type="error" messageKey="validation.serverError" />
    </I18nextProvider>,
  );

  await user.tab();
  await user.tab();
  expect(ref.current).not.toHaveFocus();

  act(() => ref.current?.focus());

  expect(ref.current).toHaveFocus();
  expect(ref.current).toHaveTextContent("Error: Something went wrong on our server.");
});
