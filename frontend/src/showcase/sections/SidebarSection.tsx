import { useId } from "react";

import { IconBell, IconFactory, IconHouse, IconPackage } from "../../icons";
import { Sidebar, type SidebarItem } from "../../layouts/Sidebar";
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

// Contenido de ejemplo del catálogo: inventado y en español (S-03), por eso lleva su propio `lang`.
export function SidebarSection() {
  const titleId = useId();
  return (
    <div role="region" aria-labelledby={titleId} lang="es" className="catalog-section">
      <h2 id={titleId}>Menú lateral</h2>
      <div className="catalog-frame">
        <Sidebar items={ITEMS} activeId="assets" />
      </div>
    </div>
  );
}
