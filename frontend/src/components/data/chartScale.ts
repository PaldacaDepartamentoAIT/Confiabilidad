export type ChartGroup = { label: string; first: number; second: number };

export type ChartScale = {
  max: number;
  ticks: number[];
  groupWidth: number;
  barWidth: number;
  // Distancia desde el borde izquierdo del grupo hasta la primera barra (las dos van centradas).
  groupOffset: number;
};

// Área de trazado dentro del lienzo de 640 × 240 (docs/identidad-visual.md, «Gráfica de barras»).
export const PLOT = { x: 40, y: 8, width: 576, height: 192 } as const;

export const TICK_STEP = 30;
export const BAR_GAP = 4;
const MAX_BAR_WIDTH = 30;
// Fracción del grupo que ocupan las dos barras con su separación: 64 de 96 px.
const BARS_SHARE = 2 / 3;

function isValid(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

// Devuelve null si no hay grupos o algún valor no es un número mayor o igual que cero.
export function chartScale(groups: readonly ChartGroup[]): ChartScale | null {
  if (groups.length === 0) return null;
  if (!groups.every((group) => isValid(group.first) && isValid(group.second))) return null;

  const largest = Math.max(...groups.flatMap((group) => [group.first, group.second]));
  const max = Math.max(TICK_STEP, Math.ceil(largest / TICK_STEP) * TICK_STEP);
  const ticks = Array.from({ length: max / TICK_STEP + 1 }, (_, i) => i * TICK_STEP);

  const groupWidth = PLOT.width / groups.length;
  const barWidth = Math.min(MAX_BAR_WIDTH, (groupWidth * BARS_SHARE - BAR_GAP) / 2);
  const groupOffset = (groupWidth - (2 * barWidth + BAR_GAP)) / 2;
  return { max, ticks, groupWidth, barWidth, groupOffset };
}
