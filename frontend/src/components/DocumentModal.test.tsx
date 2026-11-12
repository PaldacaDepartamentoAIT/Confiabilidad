import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import type { ReactNode } from "react";
import { I18nextProvider } from "react-i18next";

import { createI18n } from "../i18n";
import { DocumentModal } from "./DocumentModal";

const DOCUMENT = `# Terms\n\nSome *important* text.\n\n- First\n- Second\n\nSee [the policy](https://example.com/policy).`;

function renderModal(props: Partial<Parameters<typeof DocumentModal>[0]> = {}, footer?: ReactNode) {
  return render(
    <I18nextProvider i18n={createI18n("en")}>
      <DocumentModal
        open
        name="Terms and conditions"
        content={DOCUMENT}
        onClose={() => {}}
        {...props}
      >
        {footer ?? <input type="checkbox" aria-label="Accept" />}
      </DocumentModal>
    </I18nextProvider>,
  );
}

test("closed, it paints nothing", () => {
  const { container } = renderModal({ open: false });

  expect(container).toBeEmptyDOMElement();
  expect(document.querySelector("dialog")).toBeNull();
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("open, it is a modal dialog named after its label, painted outside the form", () => {
  const { container } = renderModal();

  const dialog = screen.getByRole("dialog", { name: "Terms and conditions" });
  expect(dialog.tagName).toBe("DIALOG");
  expect(dialog).toHaveAttribute("open");
  expect(container).not.toContainElement(dialog);
  expect(document.body).toContainElement(dialog);
});

test("it shows the close button, the document and the footer, in that order", () => {
  renderModal();

  const close = screen.getByRole("button", { name: "Close" });
  const heading = screen.getByRole("heading", { name: "Terms" });
  const footer = screen.getByRole("checkbox", { name: "Accept" });
  expect(close.compareDocumentPosition(heading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(heading.compareDocumentPosition(footer) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

test("the close button has the name of the current language", () => {
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <DocumentModal open name="Términos" content="x" onClose={() => {}}>
        <span />
      </DocumentModal>
    </I18nextProvider>,
  );
  expect(screen.getByRole("button", { name: "Cerrar" })).toBeInTheDocument();
});

test("the document keeps its format: headings, emphasis and lists", () => {
  renderModal();

  expect(screen.getByRole("heading", { level: 1, name: "Terms" })).toBeInTheDocument();
  expect(screen.getByText("important").tagName).toBe("EM");
  expect(screen.getAllByRole("listitem").map((item) => item.textContent)).toEqual([
    "First",
    "Second",
  ]);
});

test("the links of the document open in a new tab without leaving the page", () => {
  renderModal();

  const link = screen.getByRole("link", { name: "the policy" });
  expect(link).toHaveAttribute("href", "https://example.com/policy");
  expect(link).toHaveAttribute("target", "_blank");
  expect(link).toHaveAttribute("rel", "noopener noreferrer");
});

test("the scrolling part of the document can be reached with the keyboard", () => {
  renderModal();
  const body = screen.getByRole("heading", { name: "Terms" }).closest(".document-body");
  expect(body).toHaveAttribute("tabindex", "0");
});

test("it opens when the prop turns true and disappears when it turns false", () => {
  const view = renderModal({ open: false });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

  view.rerender(
    <I18nextProvider i18n={createI18n("en")}>
      <DocumentModal open name="Terms" content="x" onClose={() => {}}>
        <span />
      </DocumentModal>
    </I18nextProvider>,
  );
  expect(screen.getByRole("dialog", { name: "Terms" })).toHaveAttribute("open");

  view.rerender(
    <I18nextProvider i18n={createI18n("en")}>
      <DocumentModal open={false} name="Terms" content="x" onClose={() => {}}>
        <span />
      </DocumentModal>
    </I18nextProvider>,
  );
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("has no accessibility violations", async () => {
  renderModal();
  const results = await axe.run(document.body, { rules: { "color-contrast": { enabled: false } } });
  expect(results.violations).toEqual([]);
});

describe("closing", () => {
  it("the close button asks to close", async () => {
    const onClose = vi.fn();
    renderModal({ onClose });

    await userEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("Escape asks to close and does not close the dialog by itself", () => {
    const onClose = vi.fn();
    renderModal({ onClose });
    const dialog = screen.getByRole("dialog");
    const cancel = new Event("cancel", { cancelable: true });

    fireEvent(dialog, cancel);

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(cancel.defaultPrevented).toBe(true);
    expect(dialog).toHaveAttribute("open");
  });

  it("a click on the curtain asks to close", async () => {
    const onClose = vi.fn();
    renderModal({ onClose });

    await userEvent.click(screen.getByRole("dialog"));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("a click inside the box does not close it", async () => {
    const onClose = vi.fn();
    renderModal({ onClose });

    await userEvent.click(screen.getByRole("heading", { name: "Terms" }));
    await userEvent.click(screen.getByRole("checkbox", { name: "Accept" }));
    await userEvent.click(screen.getByRole("link", { name: "the policy" }));

    expect(onClose).not.toHaveBeenCalled();
  });

  it("other keys do not close it", async () => {
    const onClose = vi.fn();
    renderModal({ onClose });

    await userEvent.keyboard("a{Tab}{Tab}b");

    expect(onClose).not.toHaveBeenCalled();
  });
});
