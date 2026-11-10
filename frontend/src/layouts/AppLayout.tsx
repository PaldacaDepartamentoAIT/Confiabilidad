import { useCallback, useId, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type { LanguageStorage } from "../i18n/language";
import { IconMenu } from "../icons";
import { Sidebar, type SidebarItem, type SidebarUser } from "./Sidebar";
import "./AppLayout.css";

type AppLayoutProps = {
  items: readonly SidebarItem[];
  activeId?: string;
  user?: SidebarUser;
  storage?: LanguageStorage;
  topBar?: ReactNode;
  children: ReactNode;
};

// Diseño de las pantallas con sesión: menú lateral a la altura de la pantalla, barra superior y
// contenido. En pantallas de menos de 768 px el menú es un panel que abre el botón de la barra.
export function AppLayout({ items, activeId, user, storage, topBar, children }: AppLayoutProps) {
  const { t } = useTranslation();
  const sidebarId = useId();
  const opener = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);

  const close = useCallback((restoreFocus: boolean) => {
    setOpen(false);
    if (restoreFocus) opener.current?.focus();
  }, []);

  return (
    <div className="app">
      <Sidebar
        id={sidebarId}
        items={items}
        activeId={activeId}
        user={user}
        storage={storage}
        mobileOpen={open}
        onMobileClose={close}
      />
      <div className="main">
        <header className="topbar" data-ui="topbar">
          <button
            ref={opener}
            type="button"
            className="menu-btn mobile-only"
            aria-controls={sidebarId}
            aria-expanded={open}
            aria-label={t("sidebar.open")}
            onClick={() => setOpen(!open)}
          >
            <IconMenu />
          </button>
          {topBar}
        </header>
        <main className="content" data-ui="content">
          {children}
        </main>
      </div>
    </div>
  );
}
