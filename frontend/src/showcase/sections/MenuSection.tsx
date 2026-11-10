import { useId, useState } from "react";

import { LanguageButton } from "../../components/LanguageButton";
import { Menu, type MenuOption } from "../../components/menu/Menu";
import type { LanguageStorage } from "../../i18n/language";
import "./sections.css";

const PLANTS: MenuOption[] = [
  { value: "norte", label: "Norte" },
  { value: "sur", label: "Sur" },
  { value: "este", label: "Este" },
];

type MenuSectionProps = {
  storage?: LanguageStorage;
};

// Contenido de ejemplo del catálogo: inventado y en español (S-03), por eso lleva su propio `lang`.
export function MenuSection({ storage }: MenuSectionProps) {
  const titleId = useId();
  const [plant, setPlant] = useState("norte");
  const name = PLANTS.find((option) => option.value === plant)?.label;
  return (
    <div role="region" aria-labelledby={titleId} lang="es" className="catalog-section">
      <h2 id={titleId}>Menú e idioma</h2>
      <div className="catalog-grid">
        <div>
          <LanguageButton storage={storage} />
        </div>
        <div>
          <Menu
            label="Planta"
            options={PLANTS}
            value={plant}
            onSelect={setPlant}
            renderTrigger={(props) => (
              <button
                {...props}
                type="button"
                className="sb-btn hov"
                aria-label={`Planta: ${name}`}
              >
                <span className="label">Planta: {name}</span>
              </button>
            )}
          />
        </div>
      </div>
    </div>
  );
}
