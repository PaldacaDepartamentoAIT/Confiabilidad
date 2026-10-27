import type { ParseKeys } from "i18next";
import { useRef, useState, type FocusEvent, type FormEvent } from "react";
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
  fieldErrors?: Partial<Record<Field, FieldError>>;
  message?: GeneralMessage;
};

type Errors<Field extends string> = Partial<Record<Field, FieldError>>;

function firstError(validators: readonly Validator[], value: string): FieldError | null {
  for (const validate of validators) {
    const error = validate(value);
    if (error) return error;
  }
  return null;
}

function focusField(form: HTMLFormElement | null, name: string) {
  const element = form?.elements.namedItem(name);
  if (element instanceof HTMLElement) element.focus();
}

type Options = {
  processing?: boolean;
};

export function useFormValidation<Field extends string>(
  fields: Record<Field, readonly Validator[]>,
  { processing = false }: Options = {},
) {
  const { t } = useTranslation();
  const announce = useAnnouncer();
  const [localErrors, setLocalErrors] = useState<Errors<Field>>({});
  const [serverErrors, setServerErrors] = useState<Errors<Field>>({});
  const [message, setMessage] = useState<GeneralMessage | null>(null);
  const formRef = useRef<HTMLFormElement>(null);
  const messageRef = useRef<HTMLDivElement>(null);
  const names = Object.keys(fields) as Field[];

  // El error local describe el valor actual y el de servidor, el ya enviado: prevalece el local (D-14).
  const errors: Errors<Field> = { ...serverErrors, ...localErrors };

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
    return (event: FocusEvent<HTMLInputElement>) => validateField(name, event.target.value);
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
        const element = form.elements.namedItem(name);
        values[name] = element instanceof HTMLInputElement ? element.value : "";
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
    flushSync(() => {
      setServerErrors(fieldErrors);
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

  return { errors, onBlur, handleSubmit, showResult, message, formRef, messageRef };
}
