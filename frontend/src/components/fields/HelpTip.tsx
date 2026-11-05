import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";

type HelpTipProps = {
  // ID del globo, para que el campo lo tenga también en su `aria-describedby` (D-08).
  id: string;
  field: string;
  description: string;
};

export function HelpTip({ id, field, description }: HelpTipProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const pointer = useRef<string>("");

  return (
    <span className="help-tip">
      <button
        type="button"
        className="help-tip__button"
        aria-label={t("help.label", { field })}
        aria-describedby={id}
        onPointerEnter={(event) => event.pointerType === "mouse" && setOpen(true)}
        onPointerLeave={(event) => event.pointerType === "mouse" && setOpen(false)}
        onPointerDown={(event) => {
          pointer.current = event.pointerType;
        }}
        // Un toque también enfoca: lo resuelve el clic que llega después.
        onFocus={() =>
          pointer.current === "mouse" || pointer.current === "" ? setOpen(true) : undefined
        }
        onBlur={() => setOpen(false)}
        onKeyDown={(event) => event.key === "Escape" && setOpen(false)}
        // Con el ratón, el globo ya lo abrió el puntero; solo el toque lo alterna.
        onClick={() => {
          if (pointer.current !== "mouse") setOpen((current) => !current);
          pointer.current = "";
        }}
      >
        ?
      </button>
      <span id={id} role="tooltip" className="help-tip__bubble" hidden={!open}>
        {description}
      </span>
    </span>
  );
}
