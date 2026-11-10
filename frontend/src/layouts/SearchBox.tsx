import { IconSearch } from "../icons";
import "../components/fields/field.css";
import "./SearchBox.css";

type SearchBoxProps = {
  label: string;
  placeholder: string;
};

// Buscador solo visual (C-06): no filtra ni emite nada; cada pantalla que lo necesite define qué hace.
export function SearchBox({ label, placeholder }: SearchBoxProps) {
  return (
    <div className="search">
      <IconSearch />
      <input
        type="search"
        className="field"
        data-ui="search"
        aria-label={label}
        placeholder={placeholder}
        autoComplete="off"
      />
    </div>
  );
}
