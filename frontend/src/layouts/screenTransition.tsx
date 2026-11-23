import { createContext, useContext, useEffect, type RefObject } from "react";

export type TransitionPhase = "idle" | "out" | "in";

export const TransitionPhaseContext = createContext<TransitionPhase>("idle");
export const PublicShellContext = createContext(false);

export function useTransitionClass(): string | undefined {
  const phase = useContext(TransitionPhaseContext);
  return phase === "idle" ? undefined : `route-${phase}`;
}

// Anima el cambio de alto de tarjetas y bloques cuando llega su contenido asíncrono.
export function useAnimatedHeight(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof MutationObserver === "undefined") return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    let last = el.getBoundingClientRect().height;
    let timer = 0;
    const observer = new MutationObserver(() => {
      const prev = el.style.height;
      const now = el.getBoundingClientRect().height;
      el.style.transition = "none";
      el.style.height = "auto";
      const next = el.getBoundingClientRect().height;
      const from = prev ? now : last;
      if (Math.abs(next - from) < 1) {
        el.style.height = prev;
        el.style.transition = prev ? "height 0.25s ease-out" : "";
        last = next;
        return;
      }
      window.clearTimeout(timer);
      el.style.height = `${from}px`;
      el.style.overflow = "hidden";
      void el.getBoundingClientRect();
      el.style.transition = "height 0.25s ease-out";
      el.style.height = `${next}px`;
      last = next;
      timer = window.setTimeout(() => {
        el.style.height = el.style.overflow = el.style.transition = "";
        last = el.getBoundingClientRect().height;
      }, 260);
    });
    observer.observe(el, { childList: true, subtree: true, characterData: true });
    return () => {
      window.clearTimeout(timer);
      observer.disconnect();
    };
  }, [ref]);
}
