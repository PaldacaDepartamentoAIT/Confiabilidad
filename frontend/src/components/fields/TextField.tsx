import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from "react";

import { FieldShell } from "./FieldShell";

type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "required"> & {
  label: string;
  type?: "text" | "email" | "password" | "date";
  required?: boolean;
  error?: string;
  hint?: string;
  help?: string;
  adornment?: ReactNode;
};

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, type = "text", required = false, error, hint, help, adornment, ...inputProps },
  ref,
) {
  const id = useId();
  const emailProps = type === "email" ? { autoComplete: "email", inputMode: "email" as const } : {};

  return (
    <FieldShell
      id={id}
      label={label}
      required={required}
      help={help}
      hint={hint}
      error={error}
      adornment={adornment}
    >
      {(describedBy) => (
        <input
          {...emailProps}
          {...inputProps}
          ref={ref}
          id={id}
          type={type}
          aria-required={required || undefined}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
        />
      )}
    </FieldShell>
  );
});
