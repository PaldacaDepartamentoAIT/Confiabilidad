import {
  useEffect,
  useId,
  useRef,
  useState,
  type FocusEvent,
  type KeyboardEvent,
  type ReactNode,
} from "react";

export type MenuOption<Value extends string> = {
  value: Value;
  label: string;
  lang?: string;
};

type MenuButtonProps<Value extends string> = {
  label: string;
  menuLabel: string;
  options: readonly MenuOption<Value>[];
  value: Value;
  onSelect: (value: Value) => void;
  children: ReactNode;
};

// Botón con un menú de opciones exclusivas: recorrer no elige, solo Intro, Espacio o clic (D-05).
export function MenuButton<Value extends string>({
  label,
  menuLabel,
  options,
  value,
  onSelect,
  children,
}: MenuButtonProps<Value>) {
  const menuId = useId();
  const [active, setActive] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const itemRefs = useRef<(HTMLLIElement | null)[]>([]);
  const open = active !== null;
  const checked = Math.max(
    options.findIndex((option) => option.value === value),
    0,
  );

  useEffect(() => {
    if (active !== null) itemRefs.current[active]?.focus();
  }, [active]);

  function close() {
    setActive(null);
    triggerRef.current?.focus();
  }

  function choose(index: number) {
    onSelect(options[index].value);
    close();
  }

  function onTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setActive(checked);
    }
  }

  function onMenuKeyDown(event: KeyboardEvent<HTMLUListElement>) {
    if (active === null) return;
    const last = options.length - 1;
    const moves: Record<string, number> = {
      ArrowDown: active === last ? 0 : active + 1,
      ArrowUp: active === 0 ? last : active - 1,
      Home: 0,
      End: last,
    };
    if (event.key in moves) {
      event.preventDefault();
      setActive(moves[event.key]);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      choose(active);
    } else if (event.key === "Escape") {
      event.preventDefault();
      close();
    }
  }

  // Con el menú abierto el foco está siempre dentro; un clic o un foco fuera lo cierran (RF-005).
  function onBlur(event: FocusEvent<HTMLDivElement>) {
    if (!containerRef.current?.contains(event.relatedTarget as Node | null)) setActive(null);
  }

  return (
    <div ref={containerRef} className="menu-button" onBlur={onBlur}>
      <button
        ref={triggerRef}
        type="button"
        className="menu-button__trigger"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => setActive(open ? null : checked)}
        onKeyDown={onTriggerKeyDown}
      >
        {children}
      </button>
      {open && (
        <ul
          id={menuId}
          role="menu"
          aria-label={menuLabel}
          className="menu-button__menu"
          onKeyDown={onMenuKeyDown}
        >
          {options.map((option, index) => (
            <li
              key={option.value}
              ref={(node) => {
                itemRefs.current[index] = node;
              }}
              role="menuitemradio"
              aria-checked={index === checked}
              tabIndex={-1}
              lang={option.lang}
              className="menu-button__option"
              onClick={() => choose(index)}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
