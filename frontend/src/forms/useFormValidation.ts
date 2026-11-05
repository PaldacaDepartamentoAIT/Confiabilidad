import type { ParseKeys } from "i18next";
import { useEffect, useRef, useState, type FocusEvent, type FormEvent } from "react";
import { flushSync } from "react-dom";
import { useTranslation } from "react-i18next";

import type { MessageType } from "../components/FormMessage";
import { useAnnouncer } from "../components/announcer";
import type { Messages } from "../i18n/locales/en";

export type ValidationKey = keyof Messages["validation"];

// El error se guarda como clave y parámetros, no como texto, para traducirlo al pintar (D-05).
export type FieldError = {
  key: ValidationKey;
  params?: Record<string, string | number>;
};

export type Validator = (value: string) => FieldError | null;

export type GeneralMessage = {
  type: MessageType;
  messageKey: ParseKeys;
};

export type SubmitResult<Field extends string> = {
  fieldErrors?: Partial<Record<Field, FieldError | readonly FieldError[]>>;
  message?: GeneralMessage;
};

type Errors<Field extends string> = Partial<Record<Field, FieldError>>;
type ErrorLists<Field extends string> = Partial<Record<Field, readonly FieldError[]>>;

function firstError(validators: readonly Validator[], value: string): FieldError | null {
  for (const validate of validators) {
    const error = validate(value);
    if (error) return error;
  }
  return null;
}

// Una casilla vale "true" marcada y "" sin marcar, para validarla como cualquier otro campo.
function readValue(element: unknown): string {
  if (element instanceof HTMLInputElement && element.type === "checkbox") {
    return element.checked ? "true" : "";
  }
  if (element instanceof HTMLInputElement || element instanceof HTMLSelectElement) {
    return element.value;
  }
  return "";
}

function asList(error: FieldError | readonly FieldError[]): readonly FieldError[] {
  return "key" in error ? [error] : error;
}

// Si el foco se va con un clic, la validación del campo que se deja espera a que el clic termine:
// un error que aparece o desaparece desplazaría el elemento pulsado antes de soltar el botón y el
// clic caería en otro sitio. Con el teclado no hay puntero pulsado y se valida al momento.
let pointerTracked = false;
let pointerPressed = false;
const afterClick: (() => void)[] = [];

function releasePointer() {
  pointerPressed = false;
  // El clic se emite en la misma tarea que la liberación; esto corre después.
  window.setTimeout(() => afterClick.splice(0).forEach((run) => run()));
}

function trackPointer() {
  if (pointerTracked) return;
  pointerTracked = true;
  document.addEventListener("pointerdown", () => (pointerPressed = true), true);
  document.addEventListener("pointerup", releasePointer, true);
  document.addEventListener("pointercancel", releasePointer, true);
}

type Options = {
  processing?: boolean;
  scrollToError?: boolean;
};

export function useFormValidation<Field extends string>(
  fields: Record<Field, readonly Validator[]>,
  { processing = false, scrollToError = false }: Options = {},
) {
  const { t } = useTranslation();
  const announce = useAnnouncer();
  const [localErrors, setLocalErrors] = useState<Errors<Field>>({});
  const [serverErrors, setServerErrors] = useState<ErrorLists<Field>>({});
  const [message, setMessage] = useState<GeneralMessage | null>(null);
  const formRef = useRef<HTMLFormElement>(null);
  const messageRef = useRef<HTMLDivElement>(null);
  const names = Object.keys(fields) as Field[];

  useEffect(trackPointer, []);

  // El error local describe el valor actual y el de servidor, el ya enviado: prevalece el local (D-14).
  const allErrors: ErrorLists<Field> = { ...serverErrors };
  for (const name of Object.keys(localErrors) as Field[]) {
    const error = localErrors[name];
    if (error) allErrors[name] = [error];
  }
  const errors: Errors<Field> = {};
  for (const name of Object.keys(allErrors) as Field[]) {
    const first = allErrors[name]?.[0];
    if (first) errors[name] = first;
  }

  // El desplazamiento va antes del foco para que el campo quede visible aunque el navegador no lo
  // lleve a la vista al enfocarlo (RF-003).
  function focusField(form: HTMLFormElement | null, name: string) {
    const element = form?.elements.namedItem(name);
    if (!(element instanceof HTMLElement)) return;
    if (scrollToError) element.scrollIntoView({ block: "center" });
    element.focus();
  }

  function validateField(name: Field, value: string) {
    const error = firstError(fields[name], value);
    setLocalErrors((current) => {
      const next = { ...current };
      if (error) next[name] = error;
      else delete next[name];
      return next;
    });
  }

  function onBlur(name: Field) {
    return (event: FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
      const value = readValue(event.target);
      if (pointerPressed) afterClick.push(() => validateField(name, value));
      else validateField(name, value);
    };
  }

  // Los campos se buscan por su `name` y se recorren en el orden en que se declaran (orden visual).
  function handleSubmit(onValid: (values: Record<Field, string>) => void) {
    return (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (processing) return;
      const form = event.currentTarget;
      const values = {} as Record<Field, string>;
      const next: Errors<Field> = {};
      for (const name of names) {
        values[name] = readValue(form.elements.namedItem(name));
        const error = firstError(fields[name], values[name]);
        if (error) next[name] = error;
      }
      // El error se pinta antes de mover el foco, para que el lector lea el campo con su error.
      // Los errores de servidor y el mensaje general se retiran en cada envío (RF-017, RF-025).
      flushSync(() => {
        setLocalErrors(next);
        setServerErrors({});
        setMessage(null);
      });
      const firstInvalid = names.find((name) => next[name]);
      if (firstInvalid) {
        focusField(form, firstInvalid);
        return;
      }
      onValid(values);
    };
  }

  // Lo llama la pantalla con la respuesta del envío. Con errores de campo, el foco va al primero y
  // el mensaje general se anuncia sin mover el foco; sin ellos, el foco va al mensaje (RF-017).
  function showResult({ fieldErrors = {}, message: next }: SubmitResult<Field>) {
    const lists: ErrorLists<Field> = {};
    for (const name of names) {
      const error = fieldErrors[name];
      if (error) lists[name] = asList(error);
    }
    flushSync(() => {
      setServerErrors(lists);
      setMessage(next ?? null);
    });
    const firstInvalid = names.find((name) => fieldErrors[name]);
    if (firstInvalid) {
      focusField(formRef.current, firstInvalid);
      if (next) {
        announce(
          `${t(`message.${next.type}`)} ${t(next.messageKey)}`,
          next.type === "error" ? "assertive" : "polite",
        );
      }
      return;
    }
    messageRef.current?.focus();
  }

  return { errors, allErrors, onBlur, handleSubmit, showResult, message, formRef, messageRef };
}
