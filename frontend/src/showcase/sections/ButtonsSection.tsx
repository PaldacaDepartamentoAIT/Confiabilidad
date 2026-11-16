import { useId } from "react";

import { AlarmNotice } from "../../components/AlarmNotice";
import { Button } from "../../components/Button";
import { Notice } from "../../components/Notice";
import "./sections.css";

// Contenido de ejemplo del catálogo: inventado y en español (S-03), por eso lleva su propio `lang`.
export function ButtonsSection() {
  const titleId = useId();
  return (
    <div role="region" aria-labelledby={titleId} lang="es" className="catalog-section">
      <h2 id={titleId}>Botones y avisos</h2>
      <div className="catalog-row">
        <Button>Guardar</Button>
        <Button variant="secondary">Cancelar</Button>
        <Button processing>Enviar</Button>
      </div>
      <Notice role="note">Los cambios se guardan como borrador.</Notice>
      <Notice kind="success" role="note">
        Empresa guardada correctamente.
      </Notice>
      <AlarmNotice kind="p1" title="P1" action={<Button variant="secondary">Ver alarma</Button>}>
        Presión alta en el compresor C-102. Desde las 08:14.
      </AlarmNotice>
      <AlarmNotice kind="p2" title="P2">
        Temperatura alta en el motor M-07.
      </AlarmNotice>
      <AlarmNotice kind="warning" title="Advertencia">
        Vibración por encima del valor habitual en la bomba B-03.
      </AlarmNotice>
      <AlarmNotice kind="neutral" title="Mantenimiento">
        Parada programada de la línea 2 mañana a las 06:00.
      </AlarmNotice>
    </div>
  );
}
