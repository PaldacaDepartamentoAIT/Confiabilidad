import {
  useEffect,
  useId,
  useRef,
  useState,
  type ChangeEvent,
  type FocusEvent,
  type InputHTMLAttributes,
} from "react";

import { IconAlert, IconCheck } from "../../icons";
import { DocumentModal } from "../DocumentModal";
import { Checkbox } from "./Checkbox";
import "./Checkbox.css";
import "./DocumentCheckbox.css";
import "./field.css";

type DocumentCheckboxProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type" | "required" | "checked"
> & {
  // Texto de la etiqueta: es el enlace al documento y el nombre del modal.
  label: string;
  // Documento en Markdown. Sin contenido, la casilla es una casilla normal, sin enlace ni modal (RF-010).
  document?: string;
  required?: boolean;
  error?: string;
  hint?: string;
};

// Casilla de aceptación cuyo texto es un enlace que abre el documento en un modal (RF-001). No envuelve el
// texto en un `<label>`: un `<label>` marcaría la casilla al pulsar cualquier parte de la fila y aquí solo
// el cuadro la marca (D-03). Es dueña del estado marcado y lo comparte con la casilla del pie del modal (D-04).
export function DocumentCheckbox({
  label,
  document,
  required = false,
  error,
  hint,
  defaultChecked = false,
  onChange,
  onBlur,
  ...inputProps
}: DocumentCheckboxProps) {
  const id = useId();
  const linkId = `${id}-link`;
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ") || undefined;
  const link = useRef<HTMLAnchorElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const wasOpen = useRef(false);
  const [open, setOpen] = useState(false);
  const [checked, setChecked] = useState(defaultChecked);

  function change(event: ChangeEvent<HTMLInputElement>) {
    setChecked(event.target.checked);
    onChange?.(event);
  }

  // Al cerrar el modal el foco vuelve al enlace (Safari no enfoca un enlace al pulsarlo) y se pide la
  // validación al formulario con un evento cuyo objetivo es la casilla de fuera (D-05, RF-011).
  useEffect(() => {
    if (wasOpen.current && !open) {
      link.current?.focus();
      const target = input.current;
      if (target)
        onBlur?.({ target, currentTarget: target, type: "blur" } as FocusEvent<HTMLInputElement>);
    }
    wasOpen.current = open;
  }, [open, onBlur]);

  if (!document) {
    return (
      <Checkbox
        {...inputProps}
        label={label}
        required={required}
        error={error}
        hint={hint}
        checked={checked}
        onChange={change}
        onBlur={onBlur}
      />
    );
  }

  return (
    <div className="check-field">
      <div className="doc-check">
        <span className="cb">
          <input
            {...inputProps}
            ref={input}
            type="checkbox"
            data-ui="checkbox"
            aria-labelledby={linkId}
            aria-required={required || undefined}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy}
            checked={checked}
            onChange={change}
            onBlur={onBlur}
          />
          <IconCheck size={14} strokeWidth={3} />
        </span>
        <span className="txt">
          <span>
            <a
              ref={link}
              id={linkId}
              href="#"
              aria-haspopup="dialog"
              onClick={(event) => {
                event.preventDefault();
                setOpen(true);
              }}
              // Un enlace solo responde a Enter; para que la barra espaciadora lo abra, como un botón, se evita el
              // desplazamiento de la página al pulsarla y se abre al soltarla.
              onKeyDown={(event) => {
                if (event.key === " ") event.preventDefault();
              }}
              onKeyUp={(event) => {
                if (event.key === " ") setOpen(true);
              }}
            >
              {label}
            </a>
            {required && <span aria-hidden="true"> *</span>}
          </span>
        </span>
      </div>
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
      <DocumentModal open={open} name={label} content={document} onClose={() => setOpen(false)}>
        <Checkbox label={label} required={required} checked={checked} onChange={change} />
      </DocumentModal>
    </div>
  );
}
