const PAUSE_MS = 500;

function normalize(text: string): string {
  return text.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

// Búsqueda al teclear del selector (RF-017): devuelve el índice de la opción a resaltar o -1.
export function createTypeahead(now: () => number = Date.now) {
  let typed = "";
  let last = -Infinity;

  return function find(key: string, labels: readonly string[], current: number): number {
    const time = now();
    typed = time - last < PAUSE_MS ? typed + normalize(key) : normalize(key);
    last = time;
    const repeated = [...typed].every((letter) => letter === typed[0]);
    const prefix = repeated ? typed[0] : typed;
    // Repetir una letra pasa a la siguiente opción; una palabra empieza por la resaltada.
    const start = repeated ? current + 1 : current;
    for (let step = 0; step < labels.length; step++) {
      const index = (start + step) % labels.length;
      if (normalize(labels[index]).startsWith(prefix)) return index;
    }
    return -1;
  };
}
