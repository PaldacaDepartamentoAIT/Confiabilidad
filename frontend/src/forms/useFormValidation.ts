import { useState, type FocusEvent } from "react";

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

export function useFormValidation<Field extends string>(
  fields: Record<Field, readonly Validator[]>,
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

  return { errors, onBlur };
}
