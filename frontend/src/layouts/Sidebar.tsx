import { useId, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { Counter } from "../components/Block";
import { LanguageButton } from "../components/LanguageButton";
import type { LanguageStorage } from "../i18n/language";
import { IconChevronLeft, IconChevronRight, IconChevronsUpDown } from "../icons";
import { ThemeButton } from "../theme/ThemeButton";
import "../theme/ThemeButton.css";
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
  items: readonly SidebarItem[];
  activeId?: string;
  user?: SidebarUser;
  storage?: LanguageStorage;
  defaultCollapsed?: boolean;
};

export function Sidebar({
  items,
  activeId,
  user,
  storage,
  defaultCollapsed = false,
}: SidebarProps) {
  const { t } = useTranslation();
  const id = useId();
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

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
      id={id}
      className={["sidebar", collapsed && "collapsed"].filter(Boolean).join(" ")}
      data-ui="sidebar"
      aria-label={t("sidebar.label")}
    >
      <div className="sb-head" data-ui="sidebar-header">
        <p className="brand" data-ui="brand">
          {t("app.heading")}
        </p>
        <button
          type="button"
          className="menu-btn"
          data-ui="menu-toggle"
          aria-controls={id}
          aria-expanded={!collapsed}
          aria-label={collapsed ? t("sidebar.expand") : t("sidebar.collapse")}
          onClick={() => setCollapsed(!collapsed)}
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
