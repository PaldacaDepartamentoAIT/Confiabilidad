import { useId, useState, type InputHTMLAttributes } from "react";

import { IconCheck } from "../../icons";
import { DocumentModal } from "../DocumentModal";
import { Checkbox } from "./Checkbox";
import "./Checkbox.css";
import "./DocumentCheckbox.css";

type DocumentCheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "required"> & {
  // Texto de la etiqueta: es el enlace al documento y el nombre del modal.
  label: string;
  // Documento en Markdown. Sin contenido, la casilla es una casilla normal, sin enlace ni modal (RF-010).
  document?: string;
};

// Casilla de aceptación cuyo texto es un enlace que abre el documento en un modal (RF-001). No envuelve el
// texto en un `<label>`: un `<label>` marcaría la casilla al pulsar cualquier parte de la fila y aquí solo
// el cuadro la marca (D-03).
export function DocumentCheckbox({ label, document, ...inputProps }: DocumentCheckboxProps) {
  const linkId = useId();
  const [open, setOpen] = useState(false);

  if (!document) return <Checkbox label={label} {...inputProps} />;

  return (
    <div className="check-field">
      <div className="doc-check">
        <span className="cb">
          <input {...inputProps} type="checkbox" data-ui="checkbox" aria-labelledby={linkId} />
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
        {null}
      </DocumentModal>
    </div>
  );
}
