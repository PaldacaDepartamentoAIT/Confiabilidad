import { useSyncExternalStore } from "react";

// Enrutador mínimo con la API de historial (D-08): unas pocas rutas no justifican una dependencia.
export type Location = {
  path: string;
  hash: string;
};

const CHANGE = "popstate";

function subscribe(onChange: () => void): () => void {
  window.addEventListener(CHANGE, onChange);
  window.addEventListener("hashchange", onChange);
  return () => {
    window.removeEventListener(CHANGE, onChange);
    window.removeEventListener("hashchange", onChange);
  };
}

// La instantánea es una cadena para que React la compare por valor y no vuelva a pintar sin cambios.
function snapshot(): string {
  return window.location.pathname + window.location.hash;
}

export function useLocation(): Location {
  const current = useSyncExternalStore(subscribe, snapshot);
  const separator = current.indexOf("#");
  if (separator === -1) return { path: current, hash: "" };
  return { path: current.slice(0, separator), hash: current.slice(separator + 1) };
}

export function navigate(to: string): void {
  window.history.pushState(null, "", to);
  window.dispatchEvent(new PopStateEvent(CHANGE));
}

export function matchRoute<Route extends string>(
  path: string,
  routes: readonly Route[],
  fallback: Route,
): Route {
  return routes.find((route) => route === path) ?? fallback;
}
