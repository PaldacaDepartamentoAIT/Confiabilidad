import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from "react";

import { IconAlert } from "../../icons";
import "./field.css";

type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "required"> & {
  label: string;
  type?: "text" | "email" | "password" | "date";
  required?: boolean;
  error?: string;
  hint?: string;
  adornment?: ReactNode;
};

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, type = "text", required = false, error, hint, adornment, className, ...inputProps },
  ref,
) {
  const id = useId();
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ") || undefined;
  const emailProps = type === "email" ? { autoComplete: "email", inputMode: "email" as const } : {};

  return (
    <div className="fld">
      <label htmlFor={id} data-ui="field-label">
        {label}
        {required && (
          <span className="req" aria-hidden="true">
            {" "}
            *
          </span>
        )}
      </label>
      <input
        {...emailProps}
        {...inputProps}
        ref={ref}
        id={id}
        type={type}
        className={["field", className].filter(Boolean).join(" ")}
        data-ui="field"
        aria-required={required || undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
      />
      {adornment}
      {hint && (
        <p className="help" id={hintId}>
          {hint}
        </p>
      )}
      {error && (
        <p className="error-msg" id={errorId}>
          <IconAlert />
          <span>{error}</span>
        </p>
      )}
    </div>
  );
});
