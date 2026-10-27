import { useCallback, useState, type CSSProperties, type ReactNode } from "react";

import { AnnouncerContext, type Announce, type Politeness } from "./announcer";

// Fuera de la vista, pero dentro del árbol de accesibilidad.
const visuallyHidden: CSSProperties = {
  position: "absolute",
  width: 1,
  height: 1,
  margin: -1,
  padding: 0,
  border: 0,
  overflow: "hidden",
  clip: "rect(0 0 0 0)",
  whiteSpace: "nowrap",
};

export function LiveAnnouncer({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Record<Politeness, string>>({
    polite: "",
    assertive: "",
  });

  // Las regiones existen desde el inicio y se vacían antes de cada texto: los lectores solo
  // anuncian cambios en una región que ya estaba, también si se repite el mismo texto (D-08).
  const announce = useCallback<Announce>((text, politeness = "polite") => {
    setMessages((current) => ({ ...current, [politeness]: "" }));
    setTimeout(() => setMessages((current) => ({ ...current, [politeness]: text })), 0);
  }, []);

  return (
    <AnnouncerContext.Provider value={announce}>
      {children}
      <div role="status" aria-live="polite" aria-atomic="true" style={visuallyHidden}>
        {messages.polite}
      </div>
      <div aria-live="assertive" aria-atomic="true" style={visuallyHidden}>
        {messages.assertive}
      </div>
    </AnnouncerContext.Provider>
  );
}
