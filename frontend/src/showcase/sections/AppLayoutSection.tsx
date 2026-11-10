import { useId } from "react";

import { Block } from "../../components/Block";
import type { LanguageStorage } from "../../i18n/language";
import { IconBell, IconFactory, IconHouse, IconPackage } from "../../icons";
import { AppLayout } from "../../layouts/AppLayout";
import type { SidebarItem } from "../../layouts/Sidebar";
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

type AppLayoutSectionProps = {
  storage?: LanguageStorage;
};

// Contenido de ejemplo del catálogo: inventado y en español (S-03), por eso lleva su propio `lang`.
export function AppLayoutSection({ storage }: AppLayoutSectionProps) {
  const titleId = useId();
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
        >
          <h3>Activos</h3>
          <Block title="Inventario" count={248}>
            <p>Contenido de ejemplo de una pantalla con sesión.</p>
          </Block>
        </AppLayout>
      </div>
    </div>
  );
}
