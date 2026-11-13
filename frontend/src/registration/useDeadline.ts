import { useEffect, useRef } from "react";

// Llama a `onExpire` una vez si pasan `ms` con `active` verdadero. Si `active` pasa a falso, o el
// componente se desmonta, el plazo se cancela; si vuelve a ser verdadero, empieza de nuevo (RF-004).
export function useDeadline(active: boolean, ms: number, onExpire: () => void) {
  const onExpireRef = useRef(onExpire);

  useEffect(() => {
    onExpireRef.current = onExpire;
  }, [onExpire]);

  useEffect(() => {
    if (!active) return;
    const id = window.setTimeout(() => onExpireRef.current(), ms);
    return () => window.clearTimeout(id);
  }, [active, ms]);
}
