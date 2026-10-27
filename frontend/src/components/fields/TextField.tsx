import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from "react";

type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "required"> & {
  label: string;
  type?: "text" | "email" | "password";
  required?: boolean;
  error?: string;
  adornment?: ReactNode;
};

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, type = "text", required = false, error, adornment, ...inputProps },
  ref,
) {
  const id = useId();
  const errorId = `${id}-error`;
  const emailProps = type === "email" ? { autoComplete: "email", inputMode: "email" as const } : {};

  return (
    <div>
      <label htmlFor={id}>
        {label}
        {required && <span aria-hidden="true"> *</span>}
      </label>
      <input
        {...emailProps}
        {...inputProps}
        ref={ref}
        id={id}
        type={type}
        aria-required={required || undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
      />
      {adornment}
      {error && <p id={errorId}>{error}</p>}
    </div>
  );
});
