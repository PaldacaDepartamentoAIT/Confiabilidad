import { SearchBox } from "./SearchBox";
import { Tabs, type TabItem } from "./Tabs";
import "./TopBar.css";

type TopBarProps = {
  tabsLabel: string;
  tabs: readonly TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  idPrefix?: string;
  searchLabel: string;
  searchPlaceholder: string;
};

// Contenido de la barra superior de una pantalla con sesión: pestañas a la izquierda, que ocupan el
// sitio que deja el buscador, y buscador a la derecha. Va en el hueco `topBar` de `AppLayout`.
export function TopBar({
  tabsLabel,
  tabs,
  activeId,
  onChange,
  idPrefix,
  searchLabel,
  searchPlaceholder,
}: TopBarProps) {
  return (
    <>
      <div className="tabs-area">
        <div className="tabs-clip">
          <Tabs
            label={tabsLabel}
            tabs={tabs}
            activeId={activeId}
            onChange={onChange}
            idPrefix={idPrefix}
          />
        </div>
      </div>
      <SearchBox label={searchLabel} placeholder={searchPlaceholder} />
    </>
  );
}
