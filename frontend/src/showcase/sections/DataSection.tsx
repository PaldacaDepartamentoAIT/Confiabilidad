import { useId } from "react";

import { Indicator, IndicatorGrid } from "../../components/data/Indicator";
import "./sections.css";

// Contenido de ejemplo del catálogo: inventado y en español (S-03), por eso lleva su propio `lang`.
export function DataSection() {
  const titleId = useId();
  return (
    <div role="region" aria-labelledby={titleId} lang="es" className="catalog-section">
      <h2 id={titleId}>Indicadores</h2>
      <IndicatorGrid>
        <Indicator label="Activos registrados" value="248" help="12 nuevos este mes" />
        <Indicator variant="featured" label="Disponibilidad" value="96,4 %" help="Objetivo 95 %" />
        <Indicator label="Órdenes abiertas" value="37" help="9 vencen esta semana" />
        <Indicator
          variant="alert"
          label="Alarmas P1 activas"
          value="2"
          help="Requieren atención inmediata"
        />
      </IndicatorGrid>
    </div>
  );
}
