import type { ReactNode } from "react";

// Sitio de una línea reservado encima del botón principal de cada paso, haya o no mensaje (RF-023).
export function MessageZone({ children }: { children?: ReactNode }) {
  return <div className="message-zone">{children}</div>;
}
