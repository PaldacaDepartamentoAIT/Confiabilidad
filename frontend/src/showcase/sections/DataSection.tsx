import { useId } from "react";

import { Block } from "../../components/Block";
import { Chip } from "../../components/Chip";
import { BarChart } from "../../components/data/BarChart";
import type { ChartGroup } from "../../components/data/chartScale";
import { Indicator, IndicatorGrid } from "../../components/data/Indicator";
import {
  StatusGrid,
  type StatusGridCell,
  type StatusGridLabels,
} from "../../components/data/StatusGrid";
import { Table, type TableColumn, type TableRow } from "../../components/data/Table";
import "./sections.css";

const COLUMNS: TableColumn[] = [
  { key: "code", header: "Código", kind: "code" },
  { key: "name", header: "Nombre" },
  { key: "criticality", header: "Criticidad" },
  { key: "status", header: "Estado", kind: "status" },
  { key: "date", header: "Fecha", kind: "code" },
];

const ROWS: TableRow[] = [
  ["C-102", "Compresor de aire", "Alta", "Fuera de servicio", "p1", "2026-11-07"],
  ["P-017", "Bomba de proceso", "Alta", "Degradado", "p2", "2026-11-05"],
  ["H-004", "Horno de secado", "Media", "Advertencia", "warning", "2026-11-04"],
  ["B-210", "Caldera principal", "Alta", "En mantenimiento", "neutral", "2026-11-02"],
  ["V-033", "Válvula de control", "Baja", "Operativo", undefined, "2026-10-29"],
].map(([code, name, criticality, text, kind, date]) => ({
  id: String(code),
  cells: {
    code,
    name,
    criticality: <Chip>{criticality}</Chip>,
    status: { text, kind },
    date,
  },
})) as TableRow[];

const MONTHS: ChartGroup[] = [
  { label: "Jun", first: 62, second: 48 },
  { label: "Jul", first: 70, second: 44 },
  { label: "Ago", first: 78, second: 38 },
  { label: "Sep", first: 84, second: 30 },
  { label: "Oct", first: 90, second: 26 },
  { label: "Nov", first: 96, second: 22 },
];

const STATUS_LABELS: StatusGridLabels = {
  normal: "Normal",
  p1: "P1",
  p2: "P2",
  warning: "Advertencia",
  neutral: "Mantenimiento",
};

const SPECIAL = {
  5: "p2",
  11: "warning",
  17: "neutral",
  23: "p1",
  29: "warning",
  34: "neutral",
  40: "p2",
  44: "p1",
} as const;

const ASSETS: StatusGridCell[] = Array.from({ length: 48 }, (_, i) => ({
  name: `A-${100 + i * 3}`,
  kind: SPECIAL[i as keyof typeof SPECIAL],
}));

// Contenido de ejemplo del catálogo: inventado y en español (S-03), por eso lleva su propio `lang`.
export function DataSection() {
  const indicatorsId = useId();
  const tableId = useId();
  const chartId = useId();
  const gridId = useId();
  return (
    <>
      <div role="region" aria-labelledby={indicatorsId} lang="es" className="catalog-section">
        <h2 id={indicatorsId}>Indicadores</h2>
        <IndicatorGrid>
          <Indicator label="Activos registrados" value="248" help="12 nuevos este mes" />
          <Indicator
            variant="featured"
            label="Disponibilidad"
            value="96,4 %"
            help="Objetivo 95 %"
          />
          <Indicator label="Órdenes abiertas" value="37" help="9 vencen esta semana" />
          <Indicator
            variant="alert"
            label="Alarmas P1 activas"
            value="2"
            help="Requieren atención inmediata"
          />
        </IndicatorGrid>
      </div>
      <div role="region" aria-labelledby={tableId} lang="es" className="catalog-section">
        <h2 id={tableId}>Tabla</h2>
        <Block
          title="Inventario de activos"
          count={ROWS.length}
          countLabel={`${ROWS.length} activos`}
        >
          <Table
            label="Inventario de activos"
            columns={COLUMNS}
            rows={ROWS}
            emptyMessage="Sin activos"
          />
        </Block>
        <Block title="Tabla sin filas">
          <Table
            label="Activos vacíos"
            columns={COLUMNS}
            rows={[]}
            emptyMessage="Sin activos registrados"
          />
        </Block>
      </div>
      <div role="region" aria-labelledby={chartId} lang="es" className="catalog-section">
        <h2 id={chartId}>Gráfica de barras</h2>
        <Block title="Órdenes de trabajo por mes">
          <BarChart
            groups={MONTHS}
            description="Órdenes preventivas y correctivas de junio a noviembre: las preventivas suben de 62 a 96 y las correctivas bajan de 48 a 22."
          />
        </Block>
      </div>
      <div role="region" aria-labelledby={gridId} lang="es" className="catalog-section">
        <h2 id={gridId}>Rejilla de estado</h2>
        <Block title="Estado de los activos" count={ASSETS.length} countLabel="48 activos">
          <StatusGrid
            label="Rejilla de estado de 48 activos"
            cells={ASSETS}
            labels={STATUS_LABELS}
          />
        </Block>
      </div>
    </>
  );
}
