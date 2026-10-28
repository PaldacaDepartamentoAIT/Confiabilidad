import { createContext, useContext } from "react";

export type Politeness = "polite" | "assertive";

export type Announce = (text: string, politeness?: Politeness) => void;

export const AnnouncerContext = createContext<Announce>(() => {});

export function useAnnouncer(): Announce {
  return useContext(AnnouncerContext);
}
