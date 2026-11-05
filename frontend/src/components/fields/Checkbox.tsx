import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from "react";

import { ErrorSlot } from "./FieldShell";

type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "required"> & {
  label: ReactNode;
  required?: boolean;
  error?: string;
  hint?: string;
};

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(function Checkbox(
  { label, required = false, error, hint, ...inputProps },
  ref,
) {
  const id = useId();
  const hintId = `${id}-hint`;
  const describedBy =
    [hint && hintId, error && `${id}-error`].filter(Boolean).join(" ") || undefined;

  return (
    <div className="checkbox">
      <div className="checkbox__row">
        <input
          {...inputProps}
          ref={ref}
          id={id}
          type="checkbox"
          aria-required={required || undefined}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
        />
        <label htmlFor={id}>
          {label}
          {required && (
            <span className="field__required" aria-hidden="true">
              {" "}
              *
            </span>
          )}
        </label>
      </div>
      {hint && <p id={hintId}>{hint}</p>}
      <ErrorSlot id={id} error={error} />
    </div>
  );
});
