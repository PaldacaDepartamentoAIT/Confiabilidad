import { useEffect, useState } from "react";

const QUERY = "(pointer: coarse)";

// Verdadero si el puntero principal es táctil. Si el navegador no puede decirlo, se asume que sí:
// el control nativo funciona en cualquier sitio.
function readCoarse(): boolean {
  return typeof window.matchMedia === "function" ? window.matchMedia(QUERY).matches : true;
}

export function useCoarsePointer(): boolean {
  const [coarse, setCoarse] = useState(readCoarse);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const query = window.matchMedia(QUERY);
    const update = (event: { matches: boolean }) => setCoarse(event.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  return coarse;
}
