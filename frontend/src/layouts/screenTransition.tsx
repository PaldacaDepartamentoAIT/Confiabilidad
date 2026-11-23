import { createContext, useContext } from "react";

export type TransitionPhase = "idle" | "out" | "in";

export const TransitionPhaseContext = createContext<TransitionPhase>("idle");
export const PublicShellContext = createContext(false);

export function useTransitionClass(): string | undefined {
  const phase = useContext(TransitionPhaseContext);
  if (phase === "out") return "route-out";
  if (phase === "in") return "route-in";
  return undefined;
}
