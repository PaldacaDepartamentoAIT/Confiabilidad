import { useCallback, useEffect, useRef, useState } from "react";

const TICK_MS = 1000;

// Cuenta contra una hora límite y no por número de ticks: si el navegador duerme la pestaña, al
// volver muestra lo que falta de verdad (RF-006).
export function useCountdown(onZero?: () => void) {
  const [remaining, setRemaining] = useState(0);
  const [run, setRun] = useState(0);
  const deadline = useRef(0);
  const onZeroRef = useRef(onZero);

  useEffect(() => {
    onZeroRef.current = onZero;
  }, [onZero]);

  useEffect(() => {
    if (run === 0) return;
    const id = window.setInterval(() => {
      const left = Math.max(0, Math.ceil((deadline.current - Date.now()) / 1000));
      setRemaining(left);
      if (left === 0) {
        window.clearInterval(id);
        onZeroRef.current?.();
      }
    }, TICK_MS);
    return () => window.clearInterval(id);
  }, [run]);

  const start = useCallback((seconds: number) => {
    deadline.current = Date.now() + seconds * 1000;
    setRemaining(seconds);
    setRun((current) => current + 1);
  }, []);

  return { remaining, start };
}
