import {
  forwardRef,
  useEffect,
  useId,
  useRef,
  useState,
  type FocusEvent,
  type KeyboardEvent,
  type MouseEvent,
} from "react";

import { createTypeahead } from "../../forms/typeahead";
import { ChevronDownIcon } from "../icons";
import { FieldShell } from "./FieldShell";

export type SelectOption = { value: string; label: string };

type SelectFieldProps = {
  label: string;
  placeholder: string;
  options: readonly SelectOption[];
  name?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  onBlur?: (event: FocusEvent<HTMLButtonElement>) => void;
  required?: boolean;
  error?: string;
  hint?: string;
  help?: string;
};

const PAGE = 5;

// Selector propio (D-06): un botón `role="combobox"` con `name` y `value`, sin `<select>` nativo.
export const SelectField = forwardRef<HTMLButtonElement, SelectFieldProps>(function SelectField(
  {
    label,
    placeholder,
    options,
    name,
    defaultValue = "",
    onChange,
    onBlur,
    required = false,
    error,
    hint,
    help,
  },
  ref,
) {
  const id = useId();
  const listId = `${id}-list`;
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [typeahead] = useState(() => createTypeahead());
  const [chosen, setChosen] = useState(defaultValue);
  // Índice de la opción resaltada; `null` mientras la lista está cerrada.
  const [active, setActive] = useState<number | null>(null);
  const labels = options.map((option) => option.label);
  const chosenIndex = options.findIndex((option) => option.value === chosen);
  const optionId = (index: number) => `${id}-option-${index}`;

  useEffect(() => {
    if (active !== null)
      document.getElementById(optionId(active))?.scrollIntoView?.({ block: "nearest" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  function open(index: number) {
    setActive(Math.max(index, 0));
  }

  function choose(index: number) {
    const value = options[index].value;
    setChosen(value);
    onChange?.(value);
    setActive(null);
  }

  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    const { key } = event;
    const last = options.length - 1;
    const printable = key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey;

    if (active === null) {
      if (["Enter", " ", "ArrowDown", "ArrowUp"].includes(key)) {
        event.preventDefault();
        open(chosenIndex);
      } else if (printable) {
        const index = typeahead(key, labels, chosenIndex);
        if (index >= 0) {
          event.preventDefault();
          open(index);
        }
      }
      return;
    }

    const moves: Record<string, number> = {
      ArrowDown: Math.min(active + 1, last),
      ArrowUp: Math.max(active - 1, 0),
      Home: 0,
      End: last,
      PageDown: Math.min(active + PAGE, last),
      PageUp: Math.max(active - PAGE, 0),
    };
    if (key in moves) {
      event.preventDefault();
      setActive(moves[key]);
    } else if (key === "Enter" || key === " ") {
      event.preventDefault();
      choose(active);
    } else if (key === "Escape") {
      event.preventDefault();
      setActive(null);
    } else if (key === "Tab") {
      // Elige la resaltada y deja que el Tab lleve el foco al siguiente campo.
      choose(active);
    } else if (printable) {
      const index = typeahead(key, labels, active);
      if (index >= 0) {
        event.preventDefault();
        setActive(index);
      }
    }
  }

  function onControlBlur(event: FocusEvent<HTMLButtonElement>) {
    if (wrapperRef.current?.contains(event.relatedTarget as Node | null)) return;
    setActive(null);
    onBlur?.(event);
  }

  // Sin esto, el mousedown de una opción quitaría el foco al selector.
  function keepFocus(event: MouseEvent) {
    event.preventDefault();
  }

  const isOpen = active !== null;

  return (
    <div ref={wrapperRef} className="select">
      <FieldShell id={id} label={label} required={required} help={help} hint={hint} error={error}>
        {(describedBy) => (
          <>
            <button
              ref={ref}
              id={id}
              type="button"
              role="combobox"
              name={name}
              value={chosen}
              aria-haspopup="listbox"
              aria-expanded={isOpen}
              aria-controls={isOpen ? listId : undefined}
              aria-activedescendant={isOpen ? optionId(active) : undefined}
              aria-required={required || undefined}
              aria-invalid={error ? true : undefined}
              aria-describedby={describedBy}
              className="select__control"
              onClick={() => (isOpen ? setActive(null) : open(chosenIndex))}
              onKeyDown={onKeyDown}
              onBlur={onControlBlur}
            >
              <span className={chosen ? "select__value" : "select__value select__value--empty"}>
                {chosenIndex >= 0 ? labels[chosenIndex] : placeholder}
              </span>
              <ChevronDownIcon className="select__chevron" />
            </button>
            {isOpen && (
              <ul
                id={listId}
                role="listbox"
                aria-label={label}
                className="select__list"
                onMouseDown={keepFocus}
              >
                {options.map((option, index) => (
                  <li
                    key={option.value}
                    id={optionId(index)}
                    role="option"
                    aria-selected={option.value === chosen}
                    className={
                      index === active ? "select__option select__option--active" : "select__option"
                    }
                    onClick={() => {
                      choose(index);
                    }}
                  >
                    {option.label}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </FieldShell>
    </div>
  );
});
