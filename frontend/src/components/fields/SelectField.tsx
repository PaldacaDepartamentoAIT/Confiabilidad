import { forwardRef, useId, type SelectHTMLAttributes } from "react";

import { FieldShell } from "./FieldShell";

export type SelectOption = { value: string; label: string };

type SelectFieldProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, "required"> & {
  label: string;
  placeholder: string;
  options: readonly SelectOption[];
  required?: boolean;
  error?: string;
  hint?: string;
};

export const SelectField = forwardRef<HTMLSelectElement, SelectFieldProps>(function SelectField(
  { label, placeholder, options, required = false, error, hint, ...selectProps },
  ref,
) {
  const id = useId();

  return (
    <FieldShell id={id} label={label} required={required} hint={hint} error={error}>
      {(describedBy) => (
        <select
          {...selectProps}
          ref={ref}
          id={id}
          aria-required={required || undefined}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
        >
          <option value="">{placeholder}</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}
    </FieldShell>
  );
});
