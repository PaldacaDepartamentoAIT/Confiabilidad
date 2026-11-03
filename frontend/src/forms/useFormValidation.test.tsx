import { render, screen } from "@testing-library/react";
import type { FocusEvent, ReactElement } from "react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { FormMessage } from "../components/FormMessage";
import { AnnouncerContext } from "../components/announcer";
import { createI18n } from "../i18n";
import {
  useFormValidation,
  type FieldError,
  type GeneralMessage,
  type SubmitResult,
  type Validator,
} from "./useFormValidation";

const notEmpty: Validator = (value) => (value.trim() ? null : { key: "required" });
const longEnough: Validator = (value) =>
  value.length >= 3 ? null : { key: "codeIncomplete", params: { length: 3 } };

function renderInSpanish(element: ReactElement, announce = vi.fn()) {
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <AnnouncerContext.Provider value={announce}>{element}</AnnouncerContext.Provider>
    </I18nextProvider>,
  );
  return { announce };
}

let latestErrors: Partial<Record<"name" | "code", FieldError>> = {};
let latestAllErrors: Partial<Record<string, readonly FieldError[]>> = {};

function SampleForm() {
  const { errors, onBlur } = useFormValidation({
    name: [notEmpty],
    code: [notEmpty, longEnough],
  });
  latestErrors = errors;
  return (
    <form>
      <label>
        Name
        <input onBlur={onBlur("name")} />
      </label>
      <label>
        Code
        <input onBlur={onBlur("code")} />
      </label>
    </form>
  );
}

test("validates a field when leaving it, even before any submission", async () => {
  const user = userEvent.setup();
  renderInSpanish(<SampleForm />);

  await user.click(screen.getByRole("textbox", { name: "Name" }));
  await user.tab();

  expect(latestErrors).toEqual({ name: { key: "required" } });
});

test("only the field that is left is validated", async () => {
  const user = userEvent.setup();
  renderInSpanish(<SampleForm />);

  await user.click(screen.getByRole("textbox", { name: "Code" }));
  await user.keyboard("12");
  await user.tab();

  expect(latestErrors).toEqual({ code: { key: "codeIncomplete", params: { length: 3 } } });
});

test("reports the first failing rule and removes the error once the field is fixed", async () => {
  const user = userEvent.setup();
  renderInSpanish(<SampleForm />);

  const code = screen.getByRole("textbox", { name: "Code" });
  await user.click(code);
  await user.tab();
  expect(latestErrors.code).toEqual({ key: "required" });

  await user.click(code);
  await user.keyboard("123");
  await user.tab();

  expect(latestErrors).toEqual({});
});

type SubmitFormProps = {
  onValid: (values: Record<"name" | "code", string>) => void;
  processing?: boolean;
  onFieldFocus?: (event: FocusEvent<HTMLInputElement>) => void;
};

function SubmitForm({ onValid, processing = false, onFieldFocus }: SubmitFormProps) {
  const { errors, handleSubmit } = useFormValidation(
    { name: [notEmpty], code: [notEmpty, longEnough] },
    { processing },
  );
  return (
    <form onSubmit={handleSubmit(onValid)}>
      <label>
        Name
        <input name="name" aria-invalid={errors.name ? true : undefined} onFocus={onFieldFocus} />
      </label>
      <label>
        Code
        <input name="code" aria-invalid={errors.code ? true : undefined} onFocus={onFieldFocus} />
      </label>
      <button type="submit">Send</button>
    </form>
  );
}

test("submitting validates every field and focuses the first invalid one in order", async () => {
  const user = userEvent.setup();
  const onValid = vi.fn();
  const invalidWhenFocused: (string | null)[] = [];
  renderInSpanish(
    <SubmitForm
      onValid={onValid}
      onFieldFocus={(event) => invalidWhenFocused.push(event.target.getAttribute("aria-invalid"))}
    />,
  );

  await user.type(screen.getByRole("textbox", { name: "Code" }), "1");
  invalidWhenFocused.length = 0;
  await user.click(screen.getByRole("button", { name: "Send" }));

  expect(onValid).not.toHaveBeenCalled();
  expect(screen.getByRole("textbox", { name: "Name" })).toHaveFocus();
  expect(screen.getByRole("textbox", { name: "Name" })).toHaveAttribute("aria-invalid", "true");
  expect(screen.getByRole("textbox", { name: "Code" })).toHaveAttribute("aria-invalid", "true");
  expect(invalidWhenFocused).toEqual(["true"]);
});

test("submitting with Enter from a field also validates", async () => {
  const user = userEvent.setup();
  const onValid = vi.fn();
  renderInSpanish(<SubmitForm onValid={onValid} />);

  await user.type(screen.getByRole("textbox", { name: "Name" }), "Ana");
  await user.type(screen.getByRole("textbox", { name: "Code" }), "12{Enter}");

  expect(onValid).not.toHaveBeenCalled();
  expect(screen.getByRole("textbox", { name: "Code" })).toHaveFocus();
});

test("a valid submission calls the handler with the values", async () => {
  const user = userEvent.setup();
  const onValid = vi.fn();
  renderInSpanish(<SubmitForm onValid={onValid} />);

  await user.type(screen.getByRole("textbox", { name: "Name" }), "Ana");
  await user.type(screen.getByRole("textbox", { name: "Code" }), "123");
  await user.click(screen.getByRole("button", { name: "Send" }));

  expect(onValid).toHaveBeenCalledWith({ name: "Ana", code: "123" });
});

test("while processing, a new submission is ignored", async () => {
  const user = userEvent.setup();
  const onValid = vi.fn();
  renderInSpanish(<SubmitForm onValid={onValid} processing />);

  await user.type(screen.getByRole("textbox", { name: "Name" }), "Ana");
  await user.type(screen.getByRole("textbox", { name: "Code" }), "123");
  await user.click(screen.getByRole("button", { name: "Send" }));

  expect(onValid).not.toHaveBeenCalled();
});

type ResultFormProps = {
  respond: (values: Record<"name" | "code", string>) => SubmitResult<"name" | "code"> | undefined;
  scrollToError?: boolean;
};

function ResultForm({ respond, scrollToError }: ResultFormProps) {
  const { errors, allErrors, onBlur, handleSubmit, showResult, message, formRef, messageRef } =
    useFormValidation({ name: [notEmpty], code: [notEmpty, longEnough] }, { scrollToError });
  latestErrors = errors;
  latestAllErrors = allErrors;
  return (
    <>
      {message && (
        <FormMessage ref={messageRef} type={message.type} messageKey={message.messageKey} />
      )}
      <form
        ref={formRef}
        onSubmit={handleSubmit((values) => {
          const result = respond(values);
          if (result) showResult(result);
        })}
      >
        <label>
          Name
          <input name="name" onBlur={onBlur("name")} />
        </label>
        <label>
          Code
          <input name="code" onBlur={onBlur("code")} />
        </label>
        <button type="submit">Send</button>
      </form>
    </>
  );
}

function renderResultForm(respond: ResultFormProps["respond"]) {
  return renderInSpanish(<ResultForm respond={respond} />);
}

async function submitValid(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByRole("textbox", { name: "Name" }), "Ana");
  await user.type(screen.getByRole("textbox", { name: "Code" }), "123");
  await user.click(screen.getByRole("button", { name: "Send" }));
}

const tooManyAttempts: GeneralMessage = { type: "error", messageKey: "validation.tooManyAttempts" };

test("a server error stays when leaving the field and goes away on the next submission", async () => {
  const user = userEvent.setup();
  renderResultForm(vi.fn().mockReturnValueOnce({ fieldErrors: { code: { key: "serverError" } } }));

  await submitValid(user);
  expect(latestErrors).toEqual({ code: { key: "serverError" } });
  expect(screen.getByRole("textbox", { name: "Code" })).toHaveFocus();

  await user.tab({ shift: true });
  expect(latestErrors).toEqual({ code: { key: "serverError" } });

  await user.click(screen.getByRole("button", { name: "Send" }));
  expect(latestErrors).toEqual({});
});

test("a local error takes precedence over the server error of the same field", async () => {
  const user = userEvent.setup();
  renderResultForm(vi.fn().mockReturnValueOnce({ fieldErrors: { code: { key: "serverError" } } }));

  await submitValid(user);
  await user.clear(screen.getByRole("textbox", { name: "Code" }));
  await user.tab();

  expect(latestErrors).toEqual({ code: { key: "required" } });
});

test("server errors focus the first field with error in declaration order", async () => {
  const user = userEvent.setup();
  renderResultForm(
    vi.fn().mockReturnValueOnce({
      fieldErrors: { code: { key: "serverError" }, name: { key: "serverError" } },
    }),
  );

  await submitValid(user);

  expect(screen.getByRole("textbox", { name: "Name" })).toHaveFocus();
});

test("a general message without field errors receives the focus and is not announced", async () => {
  const user = userEvent.setup();
  const { announce } = renderResultForm(vi.fn().mockReturnValueOnce({ message: tooManyAttempts }));

  await submitValid(user);

  const message = screen.getByText("Demasiados intentos", { exact: false }).closest("div");
  expect(message).toHaveTextContent(
    "Error: Demasiados intentos. Espera unos minutos y vuelve a intentarlo.",
  );
  expect(message).toHaveFocus();
  expect(announce).not.toHaveBeenCalled();
});

test("with field errors, the focus goes to the field and an error message is announced urgently", async () => {
  const user = userEvent.setup();
  const { announce } = renderResultForm(
    vi.fn().mockReturnValueOnce({
      fieldErrors: { code: { key: "serverError" } },
      message: tooManyAttempts,
    }),
  );

  await submitValid(user);

  expect(screen.getByRole("textbox", { name: "Code" })).toHaveFocus();
  expect(screen.getByText("Demasiados intentos", { exact: false })).toBeInTheDocument();
  expect(announce).toHaveBeenCalledWith(
    "Error: Demasiados intentos. Espera unos minutos y vuelve a intentarlo.",
    "assertive",
  );
});

test("with field errors, a message that is not an error is announced politely", async () => {
  const user = userEvent.setup();
  const { announce } = renderResultForm(
    vi.fn().mockReturnValueOnce({
      fieldErrors: { code: { key: "serverError" } },
      message: { type: "info", messageKey: "showcase.demoInfo" },
    }),
  );

  await submitValid(user);

  expect(announce).toHaveBeenCalledWith(
    "Información: Formulario de demostración: no se envían datos.",
    "polite",
  );
});

test("the general message goes away on the next submission, even an invalid one", async () => {
  const user = userEvent.setup();
  renderResultForm(vi.fn().mockReturnValueOnce({ message: tooManyAttempts }));

  await submitValid(user);
  await user.clear(screen.getByRole("textbox", { name: "Name" }));
  await user.click(screen.getByRole("button", { name: "Send" }));

  expect(screen.queryByText("Demasiados intentos", { exact: false })).not.toBeInTheDocument();
  expect(screen.getByRole("textbox", { name: "Name" })).toHaveFocus();
});

function ChoiceForm({ onValid, scrollToError }: { onValid: () => void; scrollToError?: boolean }) {
  const { errors, allErrors, onBlur, handleSubmit } = useFormValidation(
    { country: [notEmpty], terms: [notEmpty] },
    { scrollToError },
  );
  latestErrors = errors as typeof latestErrors;
  latestAllErrors = allErrors;
  return (
    <form onSubmit={handleSubmit(onValid)}>
      <label>
        Country
        <select name="country" onBlur={onBlur("country")} defaultValue="">
          <option value="">Choose</option>
          <option value="BR">Brazil</option>
        </select>
      </label>
      <label>
        Terms
        <input type="checkbox" name="terms" onBlur={onBlur("terms")} />
      </label>
      <button type="submit">Send</button>
    </form>
  );
}

test("reads selects and checkboxes, a checkbox as true or empty", async () => {
  const user = userEvent.setup();
  const onValid = vi.fn();
  renderInSpanish(<ChoiceForm onValid={onValid} />);

  await user.click(screen.getByRole("button", { name: "Send" }));
  expect(latestErrors).toEqual({ country: { key: "required" }, terms: { key: "required" } });
  expect(screen.getByRole("combobox", { name: "Country" })).toHaveFocus();

  await user.selectOptions(screen.getByRole("combobox", { name: "Country" }), "BR");
  await user.click(screen.getByRole("checkbox", { name: "Terms" }));
  await user.click(screen.getByRole("button", { name: "Send" }));
  expect(onValid).toHaveBeenCalledWith({ country: "BR", terms: "true" });
});

test("leaving a checkbox validates whether it is checked", async () => {
  const user = userEvent.setup();
  renderInSpanish(<ChoiceForm onValid={vi.fn()} />);
  const terms = screen.getByRole("checkbox", { name: "Terms" });

  await user.click(terms);
  await user.tab();
  expect(latestErrors).toEqual({});

  await user.click(terms);
  await user.tab();
  expect(latestErrors).toEqual({ terms: { key: "required" } });
});

test("a field can show several server errors at once", async () => {
  const user = userEvent.setup();
  const both: FieldError[] = [{ key: "serverError" }, { key: "required" }];
  renderResultForm(vi.fn().mockReturnValueOnce({ fieldErrors: { code: both } }));

  await submitValid(user);

  expect(latestErrors).toEqual({ code: { key: "serverError" } });
  expect(latestAllErrors).toEqual({ code: both });
  expect(screen.getByRole("textbox", { name: "Code" })).toHaveFocus();
});

test("all the errors of each field are available, local ones as a list of one", async () => {
  const user = userEvent.setup();
  renderInSpanish(<ChoiceForm onValid={vi.fn()} />);

  await user.click(screen.getByRole("button", { name: "Send" }));

  expect(latestAllErrors).toEqual({ country: [{ key: "required" }], terms: [{ key: "required" }] });
});

describe("scrollToError", () => {
  const scrolled: { element: Element; focused: Element | null }[] = [];

  beforeEach(() => {
    scrolled.length = 0;
    Element.prototype.scrollIntoView = function (this: Element) {
      scrolled.push({ element: this, focused: document.activeElement });
    };
  });

  afterEach(() => {
    delete (Element.prototype as Partial<Element>).scrollIntoView;
  });

  it("scrolls to the first invalid field before focusing it", async () => {
    const user = userEvent.setup();
    renderInSpanish(<ChoiceForm onValid={vi.fn()} scrollToError />);
    const country = screen.getByRole("combobox", { name: "Country" });

    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(scrolled).toHaveLength(1);
    expect(scrolled[0].element).toBe(country);
    expect(scrolled[0].focused).not.toBe(country);
    expect(country).toHaveFocus();
  });

  it("also scrolls to the first field with a server error", async () => {
    const user = userEvent.setup();
    const respond = vi.fn().mockReturnValueOnce({ fieldErrors: { code: { key: "serverError" } } });
    renderInSpanish(<ResultForm respond={respond} scrollToError />);

    await submitValid(user);

    const code = screen.getByRole("textbox", { name: "Code" });
    expect(scrolled.map((entry) => entry.element)).toEqual([code]);
    expect(code).toHaveFocus();
  });

  it("does not scroll without the option", async () => {
    const user = userEvent.setup();
    renderInSpanish(<ChoiceForm onValid={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(scrolled).toEqual([]);
  });
});
