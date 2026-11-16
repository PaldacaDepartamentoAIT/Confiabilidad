import {
  forwardRef,
  useId,
  type FocusEventHandler,
  type Ref,
  type SelectHTMLAttributes,
} from "react";

import { IconAlert } from "../../icons";
import { CustomSelect } from "./CustomSelect";
import { useCoarsePointer } from "./useCoarsePointer";
import "./field.css";

export type SelectOption = { value: string; label: string };

type SelectFieldProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, "required" | "onBlur"> & {
  label: string;
  placeholder: string;
  options: readonly SelectOption[];
  required?: boolean;
  error?: string;
  hint?: string;
  onBlur?: FocusEventHandler<HTMLSelectElement | HTMLButtonElement>;
  // Solo lo usa el selector propio; el nativo avisa con `onChange`.
  onValueChange?: (value: string) => void;
};

type NativeSelectProps = Omit<SelectFieldProps, "onValueChange">;

const NativeSelect = forwardRef<HTMLSelectElement, NativeSelectProps>(function NativeSelect(
  { label, placeholder, options, required = false, error, hint, className, ...selectProps },
  ref,
) {
  const id = useId();
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ") || undefined;

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
      <select
        {...selectProps}
        ref={ref}
        id={id}
        className={["field", className].filter(Boolean).join(" ")}
        data-ui="field"
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

// Con puntero fino se usa el selector propio (RF-016); con puntero táctil, el nativo del sistema
// (RF-031), con la misma etiqueta, opciones y error.
export const SelectField = forwardRef<HTMLSelectElement | HTMLButtonElement, SelectFieldProps>(
  function SelectField({ onValueChange, ...props }, ref) {
    const coarse = useCoarsePointer();
    if (coarse) {
      return <NativeSelect {...props} ref={ref as Ref<HTMLSelectElement>} />;
    }
    const { label, placeholder, options, required, error, hint, name, onBlur } = props;
    const value = props.value === undefined ? undefined : String(props.value);
    const defaultValue = props.defaultValue === undefined ? undefined : String(props.defaultValue);
    return (
      <CustomSelect
        ref={ref as Ref<HTMLButtonElement>}
        label={label}
        placeholder={placeholder}
        options={options}
        name={name}
        value={value}
        defaultValue={defaultValue}
        onValueChange={onValueChange}
        onBlur={onBlur as FocusEventHandler<HTMLButtonElement> | undefined}
        required={required}
        error={error}
        hint={hint}
      />
    );
  },
);
