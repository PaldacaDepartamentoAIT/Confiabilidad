import { useEffect, useId, useRef, useState } from "react";

import { IconSearch } from "../icons";
import "../components/fields/field.css";
import "../theme/ThemeButton.css";
import { useMediaQuery } from "./useMediaQuery";
import "./SearchBox.css";

type SearchBoxProps = {
  label: string;
  placeholder: string;
  // Nombre del botón que abre el campo en pantallas estrechas; por defecto, el del campo.
  openLabel?: string;
};

// Buscador solo visual (C-06): no filtra ni emite nada; cada pantalla que lo necesite define qué hace.
// En pantallas de menos de 560 px se reduce a un botón con lupa que despliega el campo con una
// animación sobre las pestañas (RF-012); Escape o perder el foco lo cierran.
export function SearchBox({ label, placeholder, openLabel }: SearchBoxProps) {
  const narrow = useMediaQuery("(max-width: 559px)");
  const [open, setOpen] = useState(false);
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const toggle = useRef<HTMLButtonElement>(null);
  const returnFocus = useRef(false);
  const expanded = narrow && open;

  useEffect(() => {
    if (!narrow) setOpen(false);
  }, [narrow]);

  useEffect(() => {
    if (expanded) {
      input.current?.focus();
    } else if (returnFocus.current) {
      // El botón está oculto mientras el campo está abierto: el foco vuelve cuando ya se ve.
      returnFocus.current = false;
      toggle.current?.focus();
    }
  }, [expanded]);

  const inert = narrow && !expanded ? ({ inert: "" } as Record<string, string>) : {};

  return (
    <>
      {narrow && (
        <button
          ref={toggle}
          type="button"
          className="search-toggle hov"
          aria-label={openLabel ?? label}
          aria-expanded={expanded}
          aria-controls={id}
          onClick={() => setOpen(true)}
        >
          <IconSearch />
        </button>
      )}
      <div
        id={id}
        className={["search", narrow && "narrow", expanded && "open"].filter(Boolean).join(" ")}
        {...inert}
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape" && expanded) {
            returnFocus.current = true;
            setOpen(false);
          }
        }}
      >
        <IconSearch />
        <input
          ref={input}
          type="search"
          className="field"
          data-ui="search"
          aria-label={label}
          placeholder={placeholder}
          autoComplete="off"
        />
      </div>
    </>
  );
}
