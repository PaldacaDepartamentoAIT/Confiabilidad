import type { ReactNode } from "react";

type Descriptions = {
  hint?: string;
  error?: string;
};

// La ayuda visible y el error se leen al llegar al control, en ese orden.
function describedBy(id: string, { hint, error }: Descriptions): string | undefined {
  return [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ") || undefined;
}

// Hueco de una línea siempre presente, para que un error no cambie el alto del formulario (D-09).
export function ErrorSlot({ id, error }: { id: string; error?: string }) {
  return (
    <div className="field__error-slot">
      {error && (
        <p id={`${id}-error`} className="field__error">
          {error}
        </p>
      )}
    </div>
  );
}

type FieldShellProps = Descriptions & {
  id: string;
  label: string;
  required?: boolean;
  adornment?: ReactNode;
  // Recibe el `aria-describedby` que debe llevar el control.
  children: (describedBy: string | undefined) => ReactNode;
};

export function FieldShell({
  id,
  label,
  required = false,
  hint,
  error,
  adornment,
  children,
}: FieldShellProps) {
  return (
    <div className="field">
      <div className="field__label-row">
        <label htmlFor={id} className="field__label">
          {label}
          {required && (
            <span className="field__required" aria-hidden="true">
              {" "}
              *
            </span>
          )}
        </label>
      </div>
      <div className={adornment ? "field__control field__control--adorned" : "field__control"}>
        {children(describedBy(id, { hint, error }))}
        {adornment}
      </div>
      {hint && (
        <p id={`${id}-hint`} className="field__hint">
          {hint}
        </p>
      )}
      <ErrorSlot id={id} error={error} />
    </div>
  );
}
