import { useId } from "react";

import { Block } from "../../components/Block";
import { Chip } from "../../components/Chip";
import { AlarmShape, type AlarmKind } from "../../icons/shapes";
import "./sections.css";

const SHAPES: { kind: AlarmKind; label: string }[] = [
  { kind: "p1", label: "P1" },
  { kind: "p2", label: "P2" },
  { kind: "warning", label: "Advertencia" },
  { kind: "neutral", label: "Mantenimiento" },
];

// Contenido de ejemplo del catálogo: inventado y en español (S-03), por eso lleva su propio `lang`.
export function BlocksSection() {
  const titleId = useId();
  return (
    <div role="region" aria-labelledby={titleId} lang="es" className="catalog-section">
      <h2 id={titleId}>Bloques, etiquetas y formas de alarma</h2>
      <Block title="Bloque normal" count={3} countLabel="3 elementos">
        <p>Superficie del color de fondo con borde gris de 1 px.</p>
      </Block>
      <Block variant="featured" title="Bloque destacado">
        <p>Fondo secundario para resaltar un resumen.</p>
      </Block>
      <Block variant="alert" title="Bloque en alerta">
        <p>Relleno negro con texto blanco.</p>
      </Block>
      <div className="catalog-row">
        <Chip>Baja</Chip>
        <Chip>Media</Chip>
        <Chip>Alta</Chip>
      </div>
      <ul className="catalog-row">
        {SHAPES.map(({ kind, label }) => (
          <li key={kind}>
            <AlarmShape kind={kind} />
            {label}
          </li>
        ))}
      </ul>
    </div>
  );
}
