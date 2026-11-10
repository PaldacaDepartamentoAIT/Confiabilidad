import { useEffect, useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

import { IconChevronRight } from "../../icons";
import "./Menu.css";

export type MenuOption = { value: string; label: ReactNode; lang?: string };

export type MenuTriggerProps = {
  role: "combobox";
  "aria-haspopup": "listbox";
  "aria-expanded": boolean;
  "aria-controls": string | undefined;
  "aria-activedescendant": string | undefined;
  onClick: () => void;
  onKeyDown: (event: KeyboardEvent<HTMLButtonElement>) => void;
  onKeyUp: (event: KeyboardEvent<HTMLButtonElement>) => void;
};

type MenuProps = {
  label: string;
  options: readonly MenuOption[];
  value?: string;
  onSelect: (value: string) => void;
  renderTrigger: (props: MenuTriggerProps) => ReactNode;
  align?: "left" | "right";
};

// Menú desplegable compartido: patrón «select-only combobox» de WAI-ARIA. El foco no sale del
// disparador; la opción resaltada se señala con `aria-activedescendant` (D-05).
export function Menu({
  label,
  options,
  value,
  onSelect,
  renderTrigger,
  align = "left",
}: MenuProps) {
  const id = useId();
  const listId = `${id}-list`;
  const optionId = (index: number) => `${id}-option-${index}`;
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [shown, setShown] = useState(false);
  const [active, setActive] = useState(-1);
  const selected = options.findIndex((option) => option.value === value);
  const last = options.length - 1;

  useEffect(() => {
    if (!open) {
      setShown(false);
      return;
    }
    const frame = requestAnimationFrame(() => setShown(true));
    return () => cancelAnimationFrame(frame);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function closeOutside(event: MouseEvent) {
      if (!wrapperRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", closeOutside);
    return () => document.removeEventListener("mousedown", closeOutside);
  }, [open]);

  function openMenu() {
    setActive(options.length === 0 ? -1 : Math.max(selected, 0));
    setOpen(true);
  }

  function choose(index: number) {
    if (index < 0) return;
    onSelect(options[index].value);
    setOpen(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (!open) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
        event.preventDefault();
        openMenu();
      }
      return;
    }
    switch (event.key) {
      case "ArrowDown":
        setActive(Math.min(last, active + 1));
        break;
      case "ArrowUp":
        setActive(Math.max(0, active - 1));
        break;
      case "Home":
        setActive(options.length === 0 ? -1 : 0);
        break;
      case "End":
        setActive(last);
        break;
      case "Enter":
      case " ":
        choose(active);
        break;
      case "Escape":
        setOpen(false);
        break;
      default:
        return;
    }
    event.preventDefault();
  }

  return (
    <div
      ref={wrapperRef}
      className="select"
      onBlur={(event) => {
        if (!wrapperRef.current?.contains(event.relatedTarget as Node | null)) setOpen(false);
      }}
    >
      {renderTrigger({
        role: "combobox",
        "aria-haspopup": "listbox",
        "aria-expanded": open,
        "aria-controls": open ? listId : undefined,
        "aria-activedescendant": open && active >= 0 ? optionId(active) : undefined,
        onClick: () => (open ? setOpen(false) : openMenu()),
        onKeyDown: handleKeyDown,
        // El espacio activa el botón al soltarlo; ya se atendió al pulsarlo.
        onKeyUp: (event) => {
          if (event.key === " ") event.preventDefault();
        },
      })}
      {open && (
        <ul
          id={listId}
          role="listbox"
          aria-label={label}
          className={["menu", shown && "open", align === "right" && "menu-right"]
            .filter(Boolean)
            .join(" ")}
        >
          {options.map((option, index) => (
            <li
              key={option.value}
              id={optionId(index)}
              role="option"
              lang={option.lang}
              aria-selected={index === selected}
              className={["option", index === active && "highlight"].filter(Boolean).join(" ")}
              onMouseDown={(event) => event.preventDefault()}
              onMouseEnter={() => setActive(index)}
              onClick={() => choose(index)}
            >
              <IconChevronRight />
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
