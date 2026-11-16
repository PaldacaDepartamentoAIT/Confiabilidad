import { forwardRef, useId, useState, type FocusEventHandler } from "react";

import { IconAlert, IconChevronDown } from "../../icons";
import { Menu } from "../menu/Menu";
import "./CustomSelect.css";
import "./field.css";
import type { SelectOption } from "./SelectField";

type CustomSelectProps = {
  label: string;
  placeholder: string;
  options: readonly SelectOption[];
  name?: string;
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  onBlur?: FocusEventHandler<HTMLButtonElement>;
  required?: boolean;
  error?: string;
  hint?: string;
  // El navegador no completa un menú propio: se acepta para tener la misma API que el nativo.
  autoComplete?: string;
};

// Selector propio (D-05, D-06): el disparador es un botón con `name` y `value`, para que
// `useFormValidation` lo lea y lo enfoque como cualquier otro campo del formulario.
export const CustomSelect = forwardRef<HTMLButtonElement, CustomSelectProps>(function CustomSelect(
  {
    label,
    placeholder,
    options,
    name,
    value,
    defaultValue = "",
    onValueChange,
    onBlur,
    required = false,
    error,
    hint,
  },
  ref,
) {
  const id = useId();
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ") || undefined;
  const [inner, setInner] = useState(defaultValue);
  const current = value ?? inner;
  const selected = options.find((option) => option.value === current);

  function choose(next: string) {
    setInner(next);
    onValueChange?.(next);
  }

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
      <Menu
        label={label}
        options={options}
        value={current}
        onSelect={choose}
        renderTrigger={(props) => (
          <button
            {...props}
            ref={ref}
            id={id}
            type="button"
            name={name}
            value={current}
            className="field select-trigger"
            data-ui="field"
            aria-required={required || undefined}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy}
            onBlur={onBlur}
          >
            <span className={["value", !selected && "placeholder"].filter(Boolean).join(" ")}>
              {selected ? selected.label : placeholder}
            </span>
            <IconChevronDown />
          </button>
        )}
      />
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
