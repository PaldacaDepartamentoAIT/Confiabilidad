import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { Counter } from "../components/Block";
import { LanguageButton } from "../components/LanguageButton";
import type { LanguageStorage } from "../i18n/language";
import { IconChevronLeft, IconChevronRight, IconChevronsUpDown } from "../icons";
import { ThemeButton } from "../theme/ThemeButton";
import "../theme/ThemeButton.css";
import { useMediaQuery } from "./useMediaQuery";
import "./Sidebar.css";

export type SidebarItem = {
  id: string;
  label: string;
  href: string;
  icon: ReactNode;
  counter?: number;
  counterLabel?: string;
};

export type SidebarUser = {
  name: string;
  initials: string;
  onClick?: () => void;
};

type SidebarProps = {
  id?: string;
  items: readonly SidebarItem[];
  activeId?: string;
  user?: SidebarUser;
  storage?: LanguageStorage;
  defaultCollapsed?: boolean;
  // En pantallas de menos de 768 px el menú es un panel superpuesto que abre y cierra quien lo usa.
  mobileOpen?: boolean;
  onMobileClose?: (restoreFocus: boolean) => void;
};

export function Sidebar({
  id: idProp,
  items,
  activeId,
  user,
  storage,
  defaultCollapsed = false,
  mobileOpen = false,
  onMobileClose,
}: SidebarProps) {
  const { t } = useTranslation();
  const generatedId = useId();
  const id = idProp ?? generatedId;
  const [collapsedState, setCollapsed] = useState(defaultCollapsed);
  const narrow = useMediaQuery("(max-width: 767px)");
  const asideRef = useRef<HTMLElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  // En pantallas pequeñas no existe el estado contraído.
  const collapsed = !narrow && collapsedState;
  const panelOpen = narrow && mobileOpen;

  useEffect(() => {
    if (panelOpen) toggleRef.current?.focus();
  }, [panelOpen]);

  useEffect(() => {
    if (!narrow && mobileOpen) onMobileClose?.(false);
  }, [narrow, mobileOpen, onMobileClose]);

  useEffect(() => {
    if (!panelOpen) return;
    function closeWithEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onMobileClose?.(true);
    }
    function closeOutside(event: MouseEvent) {
      const target = event.target as Element;
      const isOpener = target.closest("[aria-controls]")?.getAttribute("aria-controls") === id;
      if (!asideRef.current?.contains(target) && !isOpener) onMobileClose?.(false);
    }
    document.addEventListener("keydown", closeWithEscape);
    document.addEventListener("mousedown", closeOutside);
    return () => {
      document.removeEventListener("keydown", closeWithEscape);
      document.removeEventListener("mousedown", closeOutside);
    };
  }, [panelOpen, id, onMobileClose]);

  const userContent = user && (
    <>
      <span className="avatar" data-ui="avatar" aria-hidden="true">
        {user.initials}
      </span>
      <span className="label">{user.name}</span>
      <IconChevronsUpDown className="user-chevrons" />
    </>
  );

  return (
    <aside
      ref={asideRef}
      id={id}
      className={["sidebar", collapsed && "collapsed", panelOpen && "mobile-open"]
        .filter(Boolean)
        .join(" ")}
      data-ui="sidebar"
      aria-label={t("sidebar.label")}
      aria-hidden={narrow && !mobileOpen ? true : undefined}
    >
      <div className="sb-head" data-ui="sidebar-header">
        <p className="brand" data-ui="brand">
          {t("app.heading")}
        </p>
        <button
          ref={toggleRef}
          type="button"
          className="menu-btn"
          data-ui="menu-toggle"
          aria-controls={id}
          aria-expanded={narrow ? undefined : !collapsed}
          aria-label={
            narrow ? t("sidebar.close") : collapsed ? t("sidebar.expand") : t("sidebar.collapse")
          }
          onClick={() => (narrow ? onMobileClose?.(true) : setCollapsed(!collapsed))}
        >
          {collapsed ? <IconChevronRight size={22} /> : <IconChevronLeft size={22} />}
        </button>
      </div>

      <nav className="sb-nav" aria-label={t("sidebar.sections")}>
        {items.map((item) => {
          const current = item.id === activeId;
          return (
            <a
              key={item.id}
              href={item.href}
              className="nav-item hov"
              data-ui={current ? "nav-item-active" : "nav-item"}
              aria-current={current ? "page" : undefined}
              title={collapsed ? item.label : undefined}
              onClick={() => narrow && onMobileClose?.(false)}
            >
              {item.icon}
              <span className="label">{item.label}</span>
              {item.counter !== undefined && (
                <Counter label={item.counterLabel}>{item.counter}</Counter>
              )}
            </a>
          );
        })}
      </nav>

      <div className="sb-foot">
        <div className="sb-row">
          <ThemeButton storage={storage} />
          <LanguageButton storage={storage} />
        </div>
        {user &&
          (user.onClick ? (
            <button type="button" className="sb-btn user-btn hov" onClick={user.onClick}>
              {userContent}
            </button>
          ) : (
            <div className="sb-btn user-btn">{userContent}</div>
          ))}
      </div>
    </aside>
  );
}
