import type { ReactNode } from "react";

import type { LanguageStorage } from "../i18n/language";
import { Sidebar, type SidebarItem, type SidebarUser } from "./Sidebar";
import "./AppLayout.css";

type AppLayoutProps = {
  items: readonly SidebarItem[];
  activeId?: string;
  user?: SidebarUser;
  storage?: LanguageStorage;
  topBar?: ReactNode;
  // Para enseñar el diseño dentro de otra página que ya tiene su `<main>` y su barra (catálogo):
  // la barra y el contenido pasan a ser bloques sin significado de zona.
  embedded?: boolean;
  children: ReactNode;
};

// Diseño de las pantallas con sesión: menú lateral a la altura de la pantalla, barra superior y
// contenido. En pantallas de menos de 768 px el menú es un panel que abre el botón de la barra.
export function AppLayout({
  items,
  activeId,
  user,
  storage,
  topBar,
  embedded = false,
  children,
}: AppLayoutProps) {
  const Bar = embedded ? "div" : "header";
  const Content = embedded ? "div" : "main";

  return (
    <div className="app">
      <Sidebar items={items} activeId={activeId} user={user} storage={storage} />
      <div className="main">
        <Bar className="topbar" data-ui="topbar">
          {topBar}
        </Bar>
        <Content className="content" data-ui="content">
          {children}
        </Content>
      </div>
    </div>
  );
}
