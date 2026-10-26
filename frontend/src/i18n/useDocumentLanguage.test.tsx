import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { I18nextProvider } from "react-i18next";

import { createI18n } from ".";
import { useDocumentLanguage } from "./useDocumentLanguage";

test("keeps the document language and title in sync with the active language", async () => {
  const i18n = createI18n("pt-BR");
  const wrapper = ({ children }: { children: ReactNode }) => (
    <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
  );

  renderHook(() => useDocumentLanguage(), { wrapper });

  expect(document.documentElement.lang).toBe("pt-BR");
  expect(document.title).toBe("Confiabilidade — Componentes");

  await act(() => i18n.changeLanguage("en"));

  expect(document.documentElement.lang).toBe("en");
  expect(document.title).toBe("Reliability — Components");
});
