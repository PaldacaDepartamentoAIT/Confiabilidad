import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import Markdown from "react-markdown";
import { useTranslation } from "react-i18next";

import "./DocumentModal.css";

type DocumentModalProps = {
  open: boolean;
  // Nombre accesible del diálogo; no se muestra como título (RF-008).
  name: string;
  // Documento en Markdown, ya cargado por la pantalla (S-01).
  content: string;
  onClose: () => void;
  // Pie del modal: la casilla de aceptación.
  children: ReactNode;
};

// Modal de documento sobre un `<dialog>` nativo: el navegador atrapa el foco, deja inerte la página y atiende
// Escape (D-01). Se pinta en `document.body` para que no pertenezca a ningún formulario.
export function DocumentModal({ open, name, content, onClose, children }: DocumentModalProps) {
  const { t } = useTranslation();
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (open && dialog.current && !dialog.current.open) dialog.current.showModal();
  }, [open]);

  if (!open) return null;

  return createPortal(
    <dialog
      ref={dialog}
      className="document-modal"
      aria-label={name}
      // Escape: el diálogo no se cierra solo; lo cierra quien lo usa al dejar de pasar `open`.
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      // El diálogo ocupa toda la pantalla y la caja va dentro: un clic sobre él mismo es un clic en la cortina.
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="document-box">
        <div className="document-head">
          <button
            type="button"
            className="document-close"
            aria-label={t("button.close")}
            onClick={onClose}
          >
            <span aria-hidden="true">×</span>
          </button>
        </div>
        <div className="document-body" tabIndex={0}>
          <Markdown
            components={{
              a: ({ href, children: label }) => (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {label}
                </a>
              ),
            }}
          >
            {content}
          </Markdown>
        </div>
        <div className="document-foot">{children}</div>
      </div>
    </dialog>,
    document.body,
  );
}
