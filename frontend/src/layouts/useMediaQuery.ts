import { useEffect, useState } from "react";

function read(query: string): boolean {
  return typeof window.matchMedia === "function" ? window.matchMedia(query).matches : false;
}

// Para lo que cambia el comportamiento según el tamaño de pantalla (D-08); el aspecto lo decide el CSS.
// Si el navegador no tiene consultas de medios, se asume una pantalla ancha.
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => read(query));

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const list = window.matchMedia(query);
    setMatches(list.matches);
    const update = (event: { matches: boolean }) => setMatches(event.matches);
    list.addEventListener("change", update);
    return () => list.removeEventListener("change", update);
  }, [query]);

  return matches;
}
