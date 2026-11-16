import type { ReactNode } from "react";

import "../components/Block.css";
import "./PublicPage.css";

type PublicPageProps = {
  title: ReactNode;
  titleId?: string;
  children: ReactNode;
};

// Contenido de una pantalla pública (docs/identidad-visual.md, «Pantallas públicas»): una columna
// centrada con un solo bloque cuyo título de pantalla es el `h1`.
export function PublicPage({ title, titleId, children }: PublicPageProps) {
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
