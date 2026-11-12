import { useId, useState } from "react";

import { Button } from "../../components/Button";
import { DocumentModal } from "../../components/DocumentModal";
import { Checkbox } from "../../components/fields/Checkbox";
import "./sections.css";

const EXAMPLE = `# Términos y condiciones

Este texto de ejemplo muestra cómo se ve un documento dentro del modal: títulos, párrafos con *énfasis*,
listas y enlaces.

- Primera condición del servicio.
- Segunda condición del servicio.
- Tercera condición, algo más larga para que se vea cómo se parte el texto en varias líneas dentro de la caja.

Puedes leer la [política de privacidad](https://example.com/privacidad) en otra pestaña.

## Más texto

Párrafo de relleno para que el contenido tenga desplazamiento. Lorem ipsum dolor sit amet, consectetur
adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.`;

// Contenido de ejemplo del catálogo: inventado y en español (S-03), por eso lleva su propio `lang`.
export function DocumentSection() {
  const titleId = useId();
  const [open, setOpen] = useState(false);
  return (
    <div role="region" aria-labelledby={titleId} lang="es" className="catalog-section">
      <h2 id={titleId}>Documento en un modal</h2>
      <div className="catalog-row">
        <Button variant="secondary" onClick={() => setOpen(true)}>
          Abrir el documento
        </Button>
      </div>
      <DocumentModal
        open={open}
        name="Términos de ejemplo"
        content={EXAMPLE}
        onClose={() => setOpen(false)}
      >
        <Checkbox label="Acepto los términos" />
      </DocumentModal>
    </div>
  );
}
