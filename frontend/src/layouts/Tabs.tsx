import { useLayoutEffect, useRef, useState, type KeyboardEvent } from "react";

import "../theme/ThemeButton.css";
import "./Tabs.css";

export type TabItem = { id: string; label: string };

type TabsProps = {
  label: string;
  tabs: readonly TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  idPrefix?: string;
};

export function tabId(prefix: string, id: string): string {
  return `${prefix}-tab-${id}`;
}

export function tabPanelId(prefix: string, id: string): string {
  return `${prefix}-panel-${id}`;
}

// Pestañas con activación al moverse con las flechas (docs/identidad-visual.md). La línea de 2 px
// de la pestaña activa se coloca midiendo la pestaña y se desplaza con una transición de 0,25 s.
export function Tabs({ label, tabs, activeId, onChange, idPrefix = "tabs" }: TabsProps) {
  const refs = useRef(new Map<string, HTMLButtonElement>());
  const [ink, setInk] = useState({ width: 0, left: 0 });

  useLayoutEffect(() => {
    const current = refs.current.get(activeId);
    if (current) setInk({ width: current.offsetWidth - 24, left: current.offsetLeft + 12 });
  }, [activeId, tabs]);

  function select(id: string, focus: boolean) {
    onChange(id);
    if (focus) refs.current.get(id)?.focus();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const last = tabs.length - 1;
    let target: number | null = null;
    if (event.key === "ArrowRight") target = index === last ? 0 : index + 1;
    else if (event.key === "ArrowLeft") target = index === 0 ? last : index - 1;
    else if (event.key === "Home") target = 0;
    else if (event.key === "End") target = last;
    if (target === null) return;
    event.preventDefault();
    select(tabs[target].id, true);
  }

  return (
    <div className="tablist" role="tablist" aria-label={label}>
      {tabs.map((tab, index) => {
        const active = tab.id === activeId;
        return (
          <button
            key={tab.id}
            ref={(element) => {
              if (element) refs.current.set(tab.id, element);
              else refs.current.delete(tab.id);
            }}
            type="button"
            className="tab hov"
            role="tab"
            id={tabId(idPrefix, tab.id)}
            aria-controls={tabPanelId(idPrefix, tab.id)}
            aria-selected={active}
            tabIndex={active ? 0 : -1}
            data-ui={active ? "tab-active" : "tab"}
            onClick={() => select(tab.id, false)}
            onKeyDown={(event) => handleKeyDown(event, index)}
          >
            {tab.label}
          </button>
        );
      })}
      <span
        className="tab-ink"
        aria-hidden="true"
        style={{ width: `${ink.width}px`, transform: `translateX(${ink.left}px)` }}
      />
    </div>
  );
}
