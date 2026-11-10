import { useEffect, useLayoutEffect, useRef, useState, type KeyboardEvent } from "react";

import { Menu } from "../components/menu/Menu";
import { IconChevronDown } from "../icons";
import "../theme/ThemeButton.css";
import { tabId, tabPanelId } from "./tabIds";
import "./Tabs.css";

export type TabItem = { id: string; label: string };

type TabsProps = {
  label: string;
  tabs: readonly TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  idPrefix?: string;
};

// Pestañas con activación al moverse con las flechas (docs/identidad-visual.md). La línea de 2 px
// de la pestaña activa se coloca midiendo la pestaña y se desplaza con una transición de 0,25 s.
export function Tabs({ label, tabs, activeId, onChange, idPrefix = "tabs" }: TabsProps) {
  const refs = useRef(new Map<string, HTMLButtonElement>());
  const areaRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const selectRef = useRef<HTMLDivElement>(null);
  const [ink, setInk] = useState({ width: 0, left: 0 });
  const [overflow, setOverflow] = useState(false);
  const overflowRef = useRef(false);
  const pendingFocus = useRef<"select" | "tabs" | null>(null);

  useLayoutEffect(() => {
    const current = refs.current.get(activeId);
    if (current) setInk({ width: current.offsetWidth - 24, left: current.offsetLeft + 12 });
  }, [activeId, tabs]);

  // Si las pestañas no caben en el área, se sustituyen por un selector con la activa (RF-011).
  useEffect(() => {
    function measure() {
      const area = areaRef.current;
      const list = listRef.current;
      if (!area || !list) return;
      const next = list.scrollWidth > area.clientWidth + 0.5;
      if (next === overflowRef.current) return;
      const hadFocus = (next ? list : selectRef.current)?.contains(document.activeElement);
      overflowRef.current = next;
      setOverflow(next);
      pendingFocus.current = hadFocus ? (next ? "select" : "tabs") : null;
    }
    measure();
    const area = areaRef.current;
    const observer =
      typeof ResizeObserver === "function" && area ? new ResizeObserver(measure) : null;
    if (observer && area) observer.observe(area);
    window.addEventListener("resize", measure);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [tabs]);

  const activeIdRef = useRef(activeId);
  activeIdRef.current = activeId;

  // El foco salta al control que pasa a verse cuando cambia entre pestañas y selector.
  useLayoutEffect(() => {
    if (pendingFocus.current === "select") {
      selectRef.current?.querySelector<HTMLElement>("[role='combobox']")?.focus();
    } else if (pendingFocus.current === "tabs") {
      refs.current.get(activeIdRef.current)?.focus();
    }
    pendingFocus.current = null;
  }, [overflow]);

  const inert = (on: boolean) => (on ? ({ inert: "" } as Record<string, string>) : {});
  const active = tabs.find((tab) => tab.id === activeId);

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
    <div className={["tabs-area", overflow && "overflow"].filter(Boolean).join(" ")} ref={areaRef}>
      <div className="tabs-clip">
        <div
          className="tablist"
          role="tablist"
          aria-label={label}
          ref={listRef}
          {...inert(overflow)}
        >
          {tabs.map((tab, index) => {
            const isActive = tab.id === activeId;
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
                aria-selected={isActive}
                tabIndex={isActive ? 0 : -1}
                data-ui={isActive ? "tab-active" : "tab"}
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
      </div>
      <div className="tab-select" ref={selectRef} {...inert(!overflow)}>
        <Menu
          label={label}
          options={tabs.map((tab) => ({ value: tab.id, label: tab.label }))}
          value={activeId}
          onSelect={(id) => select(id, false)}
          align="right"
          renderTrigger={(props) => (
            <button
              {...props}
              type="button"
              className="trigger-tab hov"
              aria-label={`${label}: ${active?.label ?? ""}`}
            >
              {active?.label}
              <IconChevronDown />
            </button>
          )}
        />
      </div>
    </div>
  );
}
