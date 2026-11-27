import { act, fireEvent, render, screen } from "@testing-library/react";
import axe from "axe-core";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../../i18n";
import { ToastProvider } from "./ToastProvider";
import { useToast, type ToastInput } from "./toastContext";

function Trigger({ input }: { input: ToastInput }) {
  const { notify } = useToast();
  return (
    <button type="button" onClick={() => notify(input)}>
      Notify
    </button>
  );
}

function renderToast(input: ToastInput) {
  return render(
    <I18nextProvider i18n={createI18n("es")}>
      <ToastProvider>
        <Trigger input={input} />
      </ToastProvider>
    </I18nextProvider>,
  );
}

test("shows notification, resets countdown on hover and leaves with animation when expired", () => {
  vi.useFakeTimers();
  try {
    renderToast({ kind: "success", message: "Guardado correctamente", durationMs: 4000 });

    fireEvent.click(screen.getByRole("button", { name: "Notify" }));
    const toast = screen.getByRole("status");
    expect(toast).toHaveTextContent("Guardado correctamente");
    expect(toast).not.toHaveClass("is-leaving");

    act(() => vi.advanceTimersByTime(3000));
    fireEvent.mouseEnter(toast);
    act(() => vi.advanceTimersByTime(5000));
    expect(screen.getByRole("status")).not.toHaveClass("is-leaving");

    fireEvent.mouseLeave(toast);
    act(() => vi.advanceTimersByTime(3900));
    expect(screen.getByRole("status")).not.toHaveClass("is-leaving");

    act(() => vi.advanceTimersByTime(100));
    expect(screen.getByRole("status")).toHaveClass("is-leaving");

    act(() => vi.advanceTimersByTime(200));
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  } finally {
    vi.useRealTimers();
  }
});

test("dismisses quickly when clicking the X close button and passes a11y", async () => {
  const { container } = renderToast({ kind: "warning", title: "Aviso", message: "Dato revisado" });
  fireEvent.click(screen.getByRole("button", { name: "Notify" }));

  const toast = screen.getByRole("status");
  expect(toast).toHaveTextContent("Aviso");
  expect(
    (await axe.run(container, { rules: { "color-contrast": { enabled: false } } })).violations,
  ).toEqual([]);

  vi.useFakeTimers();
  try {
    fireEvent.click(screen.getByRole("button", { name: "Cerrar notificación" }));
    expect(screen.getByRole("status")).toHaveClass("is-leaving");
    act(() => vi.advanceTimersByTime(200));
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  } finally {
    vi.useRealTimers();
  }
});

test("renders error toasts as assertive alerts with error accent class and reactive i18n key", () => {
  const i18n = createI18n("es");
  render(
    <I18nextProvider i18n={i18n}>
      <ToastProvider>
        <Trigger input={{ kind: "error", messageKey: "validation.serverError" }} />
      </ToastProvider>
    </I18nextProvider>,
  );

  fireEvent.click(screen.getByRole("button", { name: "Notify" }));
  const toast = screen.getByRole("alert");
  expect(toast).toHaveClass("toast", "toast-error");
  expect(toast).toHaveTextContent("Algo falló en nuestro servidor. Vuelve a intentarlo.");

  act(() => {
    void i18n.changeLanguage("en");
  });
  expect(toast).toHaveTextContent("Something went wrong on our server.");
});
