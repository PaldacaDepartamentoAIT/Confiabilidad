import { useId, useState } from "react";

import { Block } from "../../components/Block";
import type { LanguageStorage } from "../../i18n/language";
import { IconBell, IconFactory, IconHouse, IconPackage } from "../../icons";
import { AppLayout } from "../../layouts/AppLayout";
import type { SidebarItem } from "../../layouts/Sidebar";
import { tabId, tabPanelId } from "../../layouts/tabIds";
import { Tabs } from "../../layouts/Tabs";
import "./sections.css";

const ITEMS: SidebarItem[] = [
  { id: "home", label: "Inicio", href: "#inicio", icon: <IconHouse /> },
  { id: "plants", label: "Plantas", href: "#plantas", icon: <IconFactory /> },
  { id: "assets", label: "Activos", href: "#activos", icon: <IconPackage /> },
  {
    id: "alarms",
    label: "Alarmas",
    href: "#alarmas",
    icon: <IconBell />,
    counter: 3,
    counterLabel: "3 sin revisar",
  },
];

const TABS = [
  { id: "summary", label: "Resumen" },
  { id: "inventory", label: "Inventario" },
  { id: "alarms", label: "Alarmas" },
];

const PANELS: Record<string, { title: string; text: string; count: number }> = {
  summary: {
    title: "Inventario",
    text: "Contenido de ejemplo de una pantalla con sesión.",
    count: 248,
  },
  inventory: { title: "Activos registrados", text: "Lista de activos de la planta.", count: 8 },
  alarms: { title: "Alarmas activas", text: "Alarmas pendientes de revisar.", count: 3 },
};

type AppLayoutSectionProps = {
  storage?: LanguageStorage;
};

// Contenido de ejemplo del catálogo: inventado y en español (S-03), por eso lleva su propio `lang`.
export function AppLayoutSection({ storage }: AppLayoutSectionProps) {
  const titleId = useId();
  const [active, setActive] = useState("summary");
  return (
    <div role="region" aria-labelledby={titleId} lang="es" className="catalog-section">
      <h2 id={titleId}>Diseño con sesión</h2>
      <div className="catalog-frame">
        <AppLayout
          items={ITEMS}
          activeId="assets"
          user={{ name: "Laura Gómez", initials: "LG" }}
          storage={storage}
          embedded
          topBar={
            <Tabs
              label="Secciones de la pantalla"
              tabs={TABS}
              activeId={active}
              onChange={setActive}
              idPrefix="demo"
            />
          }
        >
          <h3>Activos</h3>
          {TABS.map((tab) => (
            <div
              key={tab.id}
              role="tabpanel"
              id={tabPanelId("demo", tab.id)}
              aria-labelledby={tabId("demo", tab.id)}
              hidden={tab.id !== active}
            >
              <Block title={PANELS[tab.id].title} count={PANELS[tab.id].count}>
                <p>{PANELS[tab.id].text}</p>
              </Block>
            </div>
          ))}
        </AppLayout>
      </div>
    </div>
  );
}
