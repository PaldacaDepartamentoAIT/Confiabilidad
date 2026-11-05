import { forwardRef, useId, type SelectHTMLAttributes } from "react";

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
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div>
      <label htmlFor={id}>
        {label}
        {required && <span aria-hidden="true"> *</span>}
      </label>
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
      {hint && <p id={hintId}>{hint}</p>}
      {error && <p id={errorId}>{error}</p>}
    </div>
  );
});
