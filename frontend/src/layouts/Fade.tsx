import type { ReactNode } from "react";

import "./PublicPage.css";

type FadeProps = {
  // Al cambiar, el contenido se monta de nuevo y repite el fundido de entrada.
  fadeKey: string | number;
  children: ReactNode;
};

// Envuelve un contenido de una card pública que cambia de paso (por ejemplo, del código a la
// contraseña) para que el cambio entre con el mismo fundido que la card (RF-005).
export function Fade({ fadeKey, children }: FadeProps) {
  return (
    <div key={fadeKey} className="public-fade">
      {children}
    </div>
  );
}
