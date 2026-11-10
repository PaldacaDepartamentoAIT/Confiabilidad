import { useId, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { Counter } from "../components/Block";
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

type SidebarProps = {
  items: readonly SidebarItem[];
  activeId?: string;
};

export function Sidebar({ items, activeId }: SidebarProps) {
  const { t } = useTranslation();
  const id = useId();

  return (
    <aside id={id} className="sidebar" data-ui="sidebar" aria-label={t("sidebar.label")}>
      <div className="sb-head" data-ui="sidebar-header">
        <p className="brand" data-ui="brand">
          {t("app.heading")}
        </p>
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
    </aside>
  );
}
