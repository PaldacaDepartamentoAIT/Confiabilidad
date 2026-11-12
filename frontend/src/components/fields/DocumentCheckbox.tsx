import { useId, useState, type ChangeEvent, type InputHTMLAttributes } from "react";

import { IconCheck } from "../../icons";
import { DocumentModal } from "../DocumentModal";
import { Checkbox } from "./Checkbox";
import "./Checkbox.css";
import "./DocumentCheckbox.css";

type DocumentCheckboxProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type" | "required" | "checked"
> & {
  // Texto de la etiqueta: es el enlace al documento y el nombre del modal.
  label: string;
  // Documento en Markdown. Sin contenido, la casilla es una casilla normal, sin enlace ni modal (RF-010).
  document?: string;
  required?: boolean;
};

// Casilla de aceptación cuyo texto es un enlace que abre el documento en un modal (RF-001). No envuelve el
// texto en un `<label>`: un `<label>` marcaría la casilla al pulsar cualquier parte de la fila y aquí solo
// el cuadro la marca (D-03). Es dueña del estado marcado y lo comparte con la casilla del pie del modal (D-04).
export function DocumentCheckbox({
  label,
  document,
  required = false,
  defaultChecked = false,
  onChange,
  ...inputProps
}: DocumentCheckboxProps) {
  const linkId = useId();
  const [open, setOpen] = useState(false);
  const [checked, setChecked] = useState(defaultChecked);

  function change(event: ChangeEvent<HTMLInputElement>) {
    setChecked(event.target.checked);
    onChange?.(event);
  }

  if (!document) {
    return (
      <Checkbox
        {...inputProps}
        label={label}
        required={required}
        checked={checked}
        onChange={change}
      />
    );
  }

  return (
    <div className="check-field">
      <div className="doc-check">
        <span className="cb">
          <input
            {...inputProps}
            type="checkbox"
            data-ui="checkbox"
            aria-labelledby={linkId}
            checked={checked}
            onChange={change}
          />
          <IconCheck size={14} strokeWidth={3} />
        </span>
        <span className="txt">
          <span>
            <a
              id={linkId}
              href="#"
              aria-haspopup="dialog"
              onClick={(event) => {
                event.preventDefault();
                setOpen(true);
              }}
            >
              {label}
            </a>
          </span>
        </span>
      </div>
      <DocumentModal open={open} name={label} content={document} onClose={() => setOpen(false)}>
        <Checkbox label={label} required={required} checked={checked} onChange={change} />
      </DocumentModal>
    </div>
  );
}
