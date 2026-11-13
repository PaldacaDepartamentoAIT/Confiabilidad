import type { ReactNode } from "react";

import "../components/Block.css";
import "./PublicPage.css";

type PublicPageProps = {
  title: ReactNode;
  titleId?: string;
  ready?: boolean;
  children: ReactNode;
};

// Contenido de una pantalla pública (docs/identidad-visual.md, «Pantallas públicas»): una columna
// centrada con un solo bloque cuyo título de pantalla es el `h1`. Mientras no está lista no pinta
// nada, para no mostrar una card vacía; al estarlo, la card entra con un fundido (PublicPage.css).
export function PublicPage({ title, titleId, ready = true, children }: PublicPageProps) {
  if (!ready) return null;
  return (
    <main className="public-page">
      <div className="block public-card" data-ui="block">
        <div className="blk-h">
          <h1 id={titleId} data-ui="block-title">
            {title}
          </h1>
        </div>
        {children}
      </div>
    </main>
  );
}
