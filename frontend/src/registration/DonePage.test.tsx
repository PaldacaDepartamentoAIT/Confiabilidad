import { render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { DonePage } from "./DonePage";

function renderDone() {
  return render(
    <I18nextProvider i18n={createI18n("es")}>
      <DonePage />
    </I18nextProvider>,
  );
}

test("paints its card as soon as it mounts, inside the public card that carries the fade", () => {
  renderDone();
  const heading = screen.getByRole("heading", { level: 1, name: "Cuenta creada" });
  expect(heading.closest(".public-card")).not.toBeNull();
});

test("keeps its text", () => {
  renderDone();
  expect(screen.getByText("Tu cuenta se ha creado.")).toBeInTheDocument();
});
