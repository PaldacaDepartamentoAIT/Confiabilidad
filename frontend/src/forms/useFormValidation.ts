import { useState, type FocusEvent, type FormEvent } from "react";
import { flushSync } from "react-dom";

import type { Messages } from "../i18n/locales/en";

export type ValidationKey = keyof Messages["validation"];

// El error se guarda como clave y parámetros, no como texto, para traducirlo al pintar (D-05).
export type FieldError = {
  key: ValidationKey;
  params?: Record<string, string | number>;
};

export type Validator = (value: string) => FieldError | null;

function firstError(validators: readonly Validator[], value: string): FieldError | null {
  for (const validate of validators) {
    const error = validate(value);
    if (error) return error;
  }
  return null;
}

type Options = {
  processing?: boolean;
};

export function useFormValidation<Field extends string>(
  fields: Record<Field, readonly Validator[]>,
  { processing = false }: Options = {},
) {
  const [errors, setErrors] = useState<Partial<Record<Field, FieldError>>>({});

  function validateField(name: Field, value: string) {
    const error = firstError(fields[name], value);
    setErrors((current) => {
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
      const names = Object.keys(fields) as Field[];
      const values = {} as Record<Field, string>;
      const next: Partial<Record<Field, FieldError>> = {};
      for (const name of names) {
        const element = form.elements.namedItem(name);
        values[name] = element instanceof HTMLInputElement ? element.value : "";
        const error = firstError(fields[name], values[name]);
        if (error) next[name] = error;
      }
      // El error se pinta antes de mover el foco, para que el lector lea el campo con su error.
      flushSync(() => setErrors(next));
      const firstInvalid = names.find((name) => next[name]);
      if (firstInvalid) {
        const element = form.elements.namedItem(firstInvalid);
        if (element instanceof HTMLElement) element.focus();
        return;
      }
      onValid(values);
    };
  }

  return { errors, onBlur, handleSubmit };
}
