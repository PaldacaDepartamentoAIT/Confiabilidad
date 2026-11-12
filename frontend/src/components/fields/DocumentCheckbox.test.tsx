import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { useState, type FocusEvent } from "react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { I18nextProvider, useTranslation } from "react-i18next";

import { createI18n } from "../../i18n";
import { DocumentCheckbox } from "./DocumentCheckbox";

const LABEL = "I accept the terms and conditions";

function renderCheckbox(props: Partial<Parameters<typeof DocumentCheckbox>[0]> = {}) {
  return render(
    <I18nextProvider i18n={createI18n("en")}>
      <form>
        <DocumentCheckbox
          label={LABEL}
          name="terms"
          document={"# Terms\n\nSome text."}
          {...props}
        />
      </form>
    </I18nextProvider>,
  );
}

describe("with a document", () => {
  it("shows the text of the label as a link that announces a dialog", () => {
    renderCheckbox();

    const link = screen.getByRole("link", { name: LABEL });
    expect(link).toHaveAttribute("aria-haspopup", "dialog");
    expect(screen.getByRole("checkbox", { name: LABEL })).not.toBeChecked();
  });

  it("the checkbox is named after the link, not wrapped in a label, and keeps its name for the form", () => {
    const { container } = renderCheckbox();

    expect(container.querySelector("label")).toBeNull();
    const box = screen.getByRole("checkbox");
    expect(box).toHaveAttribute("name", "terms");
    expect(box).toHaveAttribute("data-ui", "checkbox");
    expect(box.parentElement).toHaveClass("cb");
    expect(box.nextElementSibling).toHaveClass("lucide-check");
  });

  it("pressing the link opens the document without touching the checkbox", async () => {
    renderCheckbox();

    await userEvent.click(screen.getByRole("link", { name: LABEL }));

    expect(screen.getByRole("dialog", { name: LABEL })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Terms" })).toBeInTheDocument();
    expect(screen.getAllByRole("checkbox")[0]).not.toBeChecked();
    expect(window.location.hash).toBe("");
  });

  it("pressing Enter on the link opens the document", async () => {
    renderCheckbox();
    screen.getByRole("link", { name: LABEL }).focus();

    await userEvent.keyboard("{Enter}");

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("pressing the box checks and unchecks it without opening the document", async () => {
    renderCheckbox();
    const box = screen.getByRole("checkbox");

    await userEvent.click(box);
    expect(box).toBeChecked();
    await userEvent.click(box);
    expect(box).not.toBeChecked();

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("the space bar checks the box", async () => {
    renderCheckbox();
    const box = screen.getByRole("checkbox");
    box.focus();

    await userEvent.keyboard(" ");

    expect(box).toBeChecked();
  });

  it("pressing anywhere else on the row does nothing", async () => {
    const { container } = renderCheckbox();
    const row = container.querySelector(".doc-check") as HTMLElement;
    const text = container.querySelector(".txt") as HTMLElement;

    await userEvent.click(row);
    await userEvent.click(text);
    await userEvent.click(container.querySelector(".check-field") as HTMLElement);

    expect(screen.getByRole("checkbox")).not.toBeChecked();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("the checkbox goes into the data of the form when it is checked", async () => {
    const { container } = renderCheckbox();
    const form = container.querySelector("form") as HTMLFormElement;
    expect(new FormData(form).get("terms")).toBeNull();

    await userEvent.click(screen.getByRole("checkbox"));

    expect(new FormData(form).get("terms")).toBe("on");
  });
});

describe("without a document", () => {
  it.each([
    ["an empty text", ""],
    ["no document at all", undefined],
  ])("with %s it is a normal checkbox, without link or modal", async (_name, content) => {
    renderCheckbox({ document: content });

    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    const box = screen.getByRole("checkbox", { name: LABEL });
    await userEvent.click(screen.getByText(LABEL));
    expect(box).toBeChecked();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});

describe("the checkbox of the modal", () => {
  async function openIt(props: Partial<Parameters<typeof DocumentCheckbox>[0]> = {}) {
    const view = renderCheckbox(props);
    await userEvent.click(screen.getByRole("link", { name: LABEL }));
    const dialog = screen.getByRole("dialog");
    const inner = within(dialog).getByRole("checkbox", { name: LABEL });
    const outer = view.container.querySelector("input[name='terms']") as HTMLInputElement;
    return { ...view, dialog, inner, outer };
  }

  it("is in the footer of the modal with the same text and starts like the outside one", async () => {
    const { dialog, inner } = await openIt();

    expect(dialog.querySelector(".document-foot")).toContainElement(inner);
    expect(inner).not.toBeChecked();
  });

  it("starts checked when the outside one is checked", async () => {
    const { container } = renderCheckbox();
    await userEvent.click(container.querySelector("input[name='terms']") as HTMLInputElement);

    await userEvent.click(screen.getByRole("link", { name: LABEL }));

    expect(within(screen.getByRole("dialog")).getByRole("checkbox")).toBeChecked();
  });

  it("starts checked with defaultChecked", async () => {
    const { inner, outer } = await openIt({ defaultChecked: true });

    expect(outer).toBeChecked();
    expect(inner).toBeChecked();
  });

  it("pressing its text checks it, and the outside one follows", async () => {
    const { dialog, inner, outer } = await openIt();

    await userEvent.click(within(dialog).getByText(LABEL));

    expect(inner).toBeChecked();
    expect(outer).toBeChecked();
  });

  it("unchecking it unchecks the outside one", async () => {
    const { inner, outer } = await openIt({ defaultChecked: true });

    await userEvent.click(inner);

    expect(inner).not.toBeChecked();
    expect(outer).not.toBeChecked();
  });

  it("the outside one changes the inner one too while the modal is open", async () => {
    const { inner, outer } = await openIt();

    await userEvent.click(outer);

    expect(inner).toBeChecked();
  });

  it("the modal stays open when it is checked or unchecked", async () => {
    const { dialog, inner } = await openIt();

    await userEvent.click(inner);
    await userEvent.click(inner);

    expect(screen.getByRole("dialog")).toBe(dialog);
  });

  it("keeps the state when the modal is closed and opened again", async () => {
    const { inner, outer } = await openIt();
    await userEvent.click(inner);
    await userEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(outer).toBeChecked();

    await userEvent.click(screen.getByRole("link", { name: LABEL }));

    expect(within(screen.getByRole("dialog")).getByRole("checkbox")).toBeChecked();
  });

  it("shows the asterisk of the obligatory ones, only when it is obligatory", async () => {
    const required = await openIt({ required: true });
    expect(required.dialog.querySelector(".document-foot .txt")).toHaveTextContent(`${LABEL} *`);
    required.unmount();

    const optional = await openIt();
    expect(optional.dialog.querySelector(".document-foot .txt")).not.toHaveTextContent("*");
  });

  it("is outside the form and out of its data: only the outside one is sent", async () => {
    const { container, inner, outer } = await openIt();
    const form = container.querySelector("form") as HTMLFormElement;

    await userEvent.click(inner);

    expect(form).not.toContainElement(inner);
    expect(inner).not.toHaveAttribute("name");
    expect(new FormData(form).getAll("terms")).toEqual(["on"]);
    expect(outer).toBeChecked();
  });

  it("tells the form about every change, from either checkbox", async () => {
    const onChange = vi.fn();
    const { inner, outer } = await openIt({ onChange });

    await userEvent.click(outer);
    await userEvent.click(inner);

    expect(onChange).toHaveBeenCalledTimes(2);
  });
});

describe("obligatory, help, error and closing", () => {
  it("marks the obligatory one with an asterisk outside the link and with aria-required", () => {
    renderCheckbox({ required: true });

    const link = screen.getByRole("link", { name: LABEL });
    expect(link).not.toHaveTextContent("*");
    expect(link.closest(".txt")).toHaveTextContent(`${LABEL} *`);
    expect(screen.getByRole("checkbox")).toHaveAttribute("aria-required", "true");
  });

  it("an optional one has no asterisk and no aria-required", () => {
    renderCheckbox();

    expect(screen.getByRole("link").closest(".txt")).not.toHaveTextContent("*");
    expect(screen.getByRole("checkbox")).not.toHaveAttribute("aria-required");
  });

  it("shows the help and the error under the row, linked to the checkbox", () => {
    const { container } = renderCheckbox({ hint: "Read it first", error: "You must accept" });

    const box = screen.getByRole("checkbox");
    const hint = screen.getByText("Read it first");
    const error = screen.getByText("You must accept").closest(".error-msg") as HTMLElement;
    expect(hint).toHaveClass("help");
    expect(error.querySelector("svg")).toHaveClass("lucide-circle-alert");
    expect(box).toHaveAttribute("aria-invalid", "true");
    expect(box.getAttribute("aria-describedby")?.split(" ")).toEqual([hint.id, error.id]);
    expect(container.querySelector(".check-field")).toContainElement(error);
  });

  it("without error it is not invalid", () => {
    renderCheckbox();
    expect(screen.getByRole("checkbox")).not.toHaveAttribute("aria-invalid");
  });

  it("the error and the help stay outside the modal, which repeats neither", async () => {
    renderCheckbox({ hint: "Read it first", error: "You must accept" });

    await userEvent.click(screen.getByRole("link", { name: LABEL }));

    const dialog = screen.getByRole("dialog");
    expect(within(dialog).queryByText("Read it first")).not.toBeInTheDocument();
    expect(within(dialog).queryByText("You must accept")).not.toBeInTheDocument();
  });

  it("the error also works without a document", () => {
    renderCheckbox({ document: "", error: "You must accept" });
    expect(screen.getByRole("checkbox")).toHaveAttribute("aria-invalid", "true");
  });

  function Form() {
    const [error, setError] = useState<string | undefined>("You must accept");
    return (
      <I18nextProvider i18n={createI18n("en")}>
        <form>
          <DocumentCheckbox
            label={LABEL}
            name="terms"
            document="Some text"
            required
            error={error}
            onBlur={(event: FocusEvent<HTMLInputElement>) =>
              setError(event.target.checked ? undefined : "You must accept")
            }
          />
        </form>
      </I18nextProvider>
    );
  }

  it("keeps the error while the modal is open even if it is checked there, and lifts it when it closes", async () => {
    render(<Form />);
    await userEvent.click(screen.getByRole("link", { name: LABEL }));

    await userEvent.click(within(screen.getByRole("dialog")).getByRole("checkbox"));
    expect(screen.getByText("You must accept")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(screen.queryByText("You must accept")).not.toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeChecked();
  });

  it("revalidates with the current state when it closes, also when it is still unchecked", async () => {
    render(<Form />);
    await userEvent.click(screen.getByRole("link", { name: LABEL }));

    await userEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(screen.getByText("You must accept")).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).not.toBeChecked();
  });

  it("asks for the validation with an event whose target is the outside checkbox, once per closing", async () => {
    const onBlur = vi.fn();
    const { container } = renderCheckbox({ onBlur });
    await userEvent.click(screen.getByRole("link", { name: LABEL }));
    expect(onBlur).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(onBlur).toHaveBeenCalledTimes(1);
    expect(onBlur.mock.calls[0][0].target).toBe(container.querySelector("input[name='terms']"));
  });

  it.each([
    ["the close button", () => userEvent.click(screen.getByRole("button", { name: "Close" }))],
    ["the curtain", () => userEvent.click(screen.getByRole("dialog"))],
  ])("the focus goes back to the link when it closes with %s", async (_name, close) => {
    renderCheckbox();
    await userEvent.click(screen.getByRole("link", { name: LABEL }));

    await close();

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: LABEL })).toHaveFocus();
  });

  it("the focus goes back to the link even if the click did not focus it", async () => {
    renderCheckbox();
    const link = screen.getByRole("link", { name: LABEL });
    // Safari no enfoca un enlace al pulsarlo: se abre sin que el enlace tenga el foco.
    fireEvent.click(link);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(link).not.toHaveFocus();

    await userEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(link).toHaveFocus();
  });
});

describe("language and accessibility with the modal open", () => {
  const TEXTS = {
    en: { label: "I accept the terms", document: "# Terms\n\nEnglish text.", close: "Close" },
    es: {
      label: "Acepto los términos",
      document: "# Términos\n\nTexto en español.",
      close: "Cerrar",
    },
  } as const;

  function Translated() {
    const { i18n } = useTranslation();
    const texts = TEXTS[i18n.language as keyof typeof TEXTS];
    return (
      <form>
        <DocumentCheckbox label={texts.label} document={texts.document} name="terms" required />
      </form>
    );
  }

  function renderTranslated() {
    const i18n = createI18n("en");
    const view = render(
      <I18nextProvider i18n={i18n}>
        <Translated />
      </I18nextProvider>,
    );
    return { ...view, i18n };
  }

  it("changing the language with the modal open updates the texts and keeps it open", async () => {
    const { i18n } = renderTranslated();
    await userEvent.click(screen.getByRole("link", { name: TEXTS.en.label }));
    const dialog = screen.getByRole("dialog");

    await act(() => i18n.changeLanguage("es"));

    expect(screen.getByRole("dialog")).toBe(dialog);
    expect(dialog).toHaveAccessibleName(TEXTS.es.label);
    expect(within(dialog).getByRole("heading", { name: "Términos" })).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: TEXTS.es.close })).toBeInTheDocument();
    expect(within(dialog).getByRole("checkbox", { name: TEXTS.es.label })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: TEXTS.es.label })).toBeInTheDocument();
  });

  it("keeps the state of the checkbox and the focus when the language changes", async () => {
    const { i18n } = renderTranslated();
    await userEvent.click(screen.getByRole("link", { name: TEXTS.en.label }));
    const inner = within(screen.getByRole("dialog")).getByRole("checkbox");
    await userEvent.click(inner);
    inner.focus();

    await act(() => i18n.changeLanguage("es"));

    expect(within(screen.getByRole("dialog")).getByRole("checkbox")).toBeChecked();
    expect(document.querySelector("input[name='terms']")).toBeChecked();
    expect(within(screen.getByRole("dialog")).getByRole("checkbox")).toHaveFocus();
  });

  it("the whole interaction can be done with the keyboard", async () => {
    renderCheckbox({ required: true });
    const link = screen.getByRole("link", { name: LABEL });

    // Tab: la casilla y después el enlace; Enter en el enlace abre el modal.
    await userEvent.tab();
    expect(screen.getByRole("checkbox")).toHaveFocus();
    await userEvent.tab();
    expect(link).toHaveFocus();
    await userEvent.keyboard("{Enter}");
    const dialog = screen.getByRole("dialog");

    // Dentro del modal: Tab recorre la «×», el contenido, y la casilla; Espacio la marca.
    const close = within(dialog).getByRole("button", { name: "Close" });
    const body = dialog.querySelector(".document-body") as HTMLElement;
    const inner = within(dialog).getByRole("checkbox");
    close.focus();
    await userEvent.tab();
    expect(body).toHaveFocus();
    await userEvent.tab();
    expect(inner).toHaveFocus();
    await userEvent.keyboard(" ");
    expect(inner).toBeChecked();

    // Escape (el evento `cancel` del navegador) cierra y devuelve el foco al enlace.
    fireEvent(dialog, new Event("cancel", { cancelable: true }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(link).toHaveFocus();
    expect(screen.getByRole("checkbox")).toBeChecked();
  });

  it.each([
    ["with the modal closed", false],
    ["with the modal open", true],
  ])("has no accessibility violations %s", async (_name, open) => {
    renderCheckbox({ required: true, hint: "Read it first", error: "You must accept" });
    if (open) await userEvent.click(screen.getByRole("link", { name: LABEL }));

    // Con el modal abierto la página de detrás queda inerte en un navegador real (lo comprueba Chromium); aquí
    // axe, que en jsdom no ve esa inertización, se limita al diálogo.
    const context = open ? (screen.getByRole("dialog") as HTMLElement) : document.body;
    const results = await axe.run(context, {
      rules: { "color-contrast": { enabled: false }, region: { enabled: false } },
    });

    expect(results.violations).toEqual([]);
  });

  it("has no accessibility violations without a document either", async () => {
    renderCheckbox({ document: "", required: true, error: "You must accept" });
    const results = await axe.run(document.body, {
      rules: { "color-contrast": { enabled: false }, region: { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });
});
