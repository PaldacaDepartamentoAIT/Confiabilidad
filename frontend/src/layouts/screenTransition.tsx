import { createContext, useContext, useEffect, type RefObject } from "react";

export type TransitionPhase = "idle" | "out" | "in";

export const TransitionPhaseContext = createContext<TransitionPhase>("idle");
export const PublicShellContext = createContext(false);

export function useTransitionClass(): string | undefined {
  const phase = useContext(TransitionPhaseContext);
  return phase === "idle" ? undefined : `route-${phase}`;
}

const collectTargets = (records: MutationRecord[], root: HTMLElement) => {
  const out = new Set<HTMLElement>();
  const push = (n: Element) =>
    n instanceof HTMLElement && !n.classList.contains("blk-h") && out.add(n);
  for (const { addedNodes, target } of records) {
    for (const n of addedNodes) {
      if (!(n instanceof HTMLElement)) continue;
      if (n.tagName === "FORM") [...n.children].forEach(push);
      else if (target === root || n.tagName === "TR") push(n);
    }
  }
  return [...out];
};

// Anima el alto de tarjetas y bloques y muestra progresivamente los elementos nuevos al cargar datos.
export function useAnimatedHeight(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const el = ref.current;
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (!el || typeof MutationObserver === "undefined" || reduced) return;
    const s = el.style;
    const set = (h: string, o = "", t = "") =>
      Object.assign(s, { height: h, overflow: o, transition: t });
    let [last, timer, raf] = [el.getBoundingClientRect().height, 0, 0];
    const stop = () => (window.clearTimeout(timer), window.cancelAnimationFrame(raf));
    const observer = new MutationObserver((records) => {
      const [prev, prevTransition] = [s.height, s.transition];
      const now = el.getBoundingClientRect().height;
      set("auto", s.overflow, "none");
      const next = el.getBoundingClientRect().height;
      const from = prev ? now : last;
      if (Math.abs(next - from) < 1) {
        set(prev, s.overflow, prev ? prevTransition : "");
        last = next;
        return;
      }
      stop();
      const items = collectTargets(records, el);
      items.forEach((n, i) => {
        n.style.animationDelay = `${Math.min(i, 10) * 55}ms`;
        n.classList.add("reveal-item");
      });
      const duration = Math.min(540, Math.max(300, 220 + Math.max(0, items.length - 1) * 55));
      set(`${from}px`, "hidden");
      last = next;
      const trans = `height ${duration}ms cubic-bezier(0.22, 1, 0.36, 1)`;
      raf = requestAnimationFrame(
        () => (raf = requestAnimationFrame(() => set(`${next}px`, "hidden", trans))),
      );
      timer = window.setTimeout(() => {
        set("");
        last = el.getBoundingClientRect().height;
      }, duration + 60);
    });
    observer.observe(el, { childList: true, subtree: true, characterData: true });
    return () => (stop(), observer.disconnect());
  }, [ref]);
}
