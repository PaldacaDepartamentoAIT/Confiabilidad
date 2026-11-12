import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

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
