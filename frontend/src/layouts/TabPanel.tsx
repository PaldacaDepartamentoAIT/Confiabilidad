import { useEffect, useRef, useState, type ComponentPropsWithoutRef } from "react";

import { tabId, tabPanelId } from "./tabIds";
import "./TabPanel.css";

type TabPanelProps = Omit<ComponentPropsWithoutRef<"div">, "id"> & {
  idPrefix: string;
  id: string;
  active: boolean;
};

// Panel de una pestaña: solo el activo es visible, y al pasar a serlo aparece con un fundido de 0,2 s
// (no al montarse). Con movimiento reducido, `base.css` quita la animación.
export function TabPanel({ idPrefix, id, active, className, children, ...rest }: TabPanelProps) {
  const [entering, setEntering] = useState(false);
  const mounted = useRef(false);

  useEffect(() => {
    if (mounted.current) setEntering(active);
    mounted.current = true;
  }, [active]);

  return (
    <div
      {...rest}
      role="tabpanel"
      id={tabPanelId(idPrefix, id)}
      aria-labelledby={tabId(idPrefix, id)}
      hidden={!active}
      className={[className, entering && "entering"].filter(Boolean).join(" ") || undefined}
    >
      {children}
    </div>
  );
}
