import { useId } from "react";

import { BAR_GAP, PLOT, chartScale, type ChartGroup } from "./chartScale";
import "./BarChart.css";

type BarChartProps = {
  groups: readonly ChartGroup[];
  // Texto alternativo que describe los datos, para quien no ve la gráfica.
  description: string;
};

// Gráfica de barras de dos series dibujada en SVG propio, sin librería (docs/identidad-visual.md).
export function BarChart({ groups, description }: BarChartProps) {
  const gridId = `grid-${useId().replace(/:/g, "")}`;
  const scale = chartScale(groups);

  if (!scale) return null;

  const { max, ticks, groupWidth, barWidth, groupOffset } = scale;
  const bottom = PLOT.y + PLOT.height;
  const heightOf = (value: number) => (value / max) * PLOT.height;

  return (
    <svg
      className="chart"
      data-ui="bar-chart"
      viewBox="0 0 640 240"
      width="100%"
      role="img"
      aria-label={description}
    >
      <defs>
        <pattern
          id={gridId}
          x={PLOT.x}
          y={PLOT.y}
          width="16"
          height="16"
          patternUnits="userSpaceOnUse"
        >
          <path d="M16 0V16M0 16H16" fill="none" stroke="var(--grid)" strokeWidth="1" />
        </pattern>
      </defs>
      <rect
        data-grid=""
        x={PLOT.x}
        y={PLOT.y}
        width={PLOT.width}
        height={PLOT.height}
        fill={`url(#${gridId})`}
      />
      {ticks.map((tick) => (
        <text
          key={tick}
          data-tick=""
          x={PLOT.x - 8}
          y={bottom - heightOf(tick) + 4}
          textAnchor="end"
        >
          {tick}
        </text>
      ))}
      {groups.map((group, index) => {
        const x = PLOT.x + index * groupWidth + groupOffset;
        const firstHeight = heightOf(group.first);
        const secondHeight = heightOf(group.second);
        return (
          <g key={index}>
            <rect
              data-series="first"
              x={x}
              y={bottom - firstHeight}
              width={barWidth}
              height={firstHeight}
              fill="var(--primary)"
            />
            <rect
              data-series="second"
              x={x + barWidth + BAR_GAP}
              y={bottom - secondHeight}
              width={barWidth}
              height={secondHeight}
              fill="var(--gray)"
            />
            <text
              data-label=""
              className="m"
              x={PLOT.x + index * groupWidth + groupWidth / 2}
              y={bottom + 20}
              textAnchor="middle"
            >
              {group.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
