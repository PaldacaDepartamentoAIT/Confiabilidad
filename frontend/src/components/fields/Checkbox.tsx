import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from "react";

import { IconAlert, IconCheck } from "../../icons";
import "./Checkbox.css";
import "./field.css";

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
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="check-field">
      <label className="check" htmlFor={id}>
        <span className="cb">
          <input
            {...inputProps}
            ref={ref}
            id={id}
            type="checkbox"
            data-ui="checkbox"
            aria-required={required || undefined}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy}
          />
          <IconCheck size={14} strokeWidth={3} />
        </span>
        <span className="txt">
          <span>
            {label}
            {required && <span aria-hidden="true"> *</span>}
          </span>
        </span>
      </label>
      {hint && (
        <p className="help" id={hintId} data-ui="help">
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
