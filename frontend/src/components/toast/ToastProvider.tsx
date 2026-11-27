import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { IconAlert, IconCheck, IconInfo, IconX } from "../../icons";
import {
  DEFAULT_TOAST_DURATION_MS,
  ToastContext,
  type ToastController,
  type ToastInput,
  type ToastKind,
} from "./toastContext";
import "./Toast.css";

type ToastEntry = {
  id: string;
  kind: ToastKind;
  title?: string;
  message: string;
  leaving: boolean;
};

const EXIT_DURATION_MS = 200;

function ToastIcon({ kind }: { kind: ToastKind }) {
  if (kind === "success") return <IconCheck />;
  if (kind === "warning" || kind === "error") return <IconAlert />;
  return <IconInfo />;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const [items, setItems] = useState<ToastEntry[]>([]);
  const autoTimers = useRef(new Map<string, number>());
  const exitTimers = useRef(new Map<string, number>());
  const durations = useRef(new Map<string, number>());
  const counter = useRef(0);

  const clearAuto = useCallback((id: string) => {
    const timer = autoTimers.current.get(id);
    if (timer !== undefined) {
      window.clearTimeout(timer);
      autoTimers.current.delete(id);
    }
  }, []);

  const clearExit = useCallback((id: string) => {
    const timer = exitTimers.current.get(id);
    if (timer !== undefined) {
      window.clearTimeout(timer);
      exitTimers.current.delete(id);
    }
  }, []);

  const remove = useCallback(
    (id: string) => {
      clearAuto(id);
      clearExit(id);
      durations.current.delete(id);
      setItems((cur) => cur.filter((item) => item.id !== id));
    },
    [clearAuto, clearExit],
  );

  const dismiss = useCallback(
    (id: string) => {
      clearAuto(id);
      if (exitTimers.current.has(id)) return;
      if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
        remove(id);
        return;
      }
      setItems((cur) => cur.map((item) => (item.id === id ? { ...item, leaving: true } : item)));
      exitTimers.current.set(
        id,
        window.setTimeout(() => remove(id), EXIT_DURATION_MS),
      );
    },
    [clearAuto, remove],
  );

  const scheduleAuto = useCallback(
    (id: string, durationMs: number) => {
      clearAuto(id);
      if (!Number.isFinite(durationMs) || durationMs <= 0) return;
      autoTimers.current.set(
        id,
        window.setTimeout(() => dismiss(id), durationMs),
      );
    },
    [clearAuto, dismiss],
  );

  const pause = useCallback(
    (id: string) => {
      clearAuto(id);
      if (exitTimers.current.has(id)) {
        clearExit(id);
        setItems((cur) => cur.map((item) => (item.id === id ? { ...item, leaving: false } : item)));
      }
    },
    [clearAuto, clearExit],
  );

  const resume = useCallback(
    (id: string) => {
      const duration = durations.current.get(id);
      if (duration !== undefined) scheduleAuto(id, duration);
    },
    [scheduleAuto],
  );

  const notify = useCallback(
    ({ kind = "info", title, message, durationMs = DEFAULT_TOAST_DURATION_MS }: ToastInput) => {
      counter.current += 1;
      const id = `toast-${counter.current}`;
      durations.current.set(id, durationMs);
      setItems((cur) => [...cur, { id, kind, title, message, leaving: false }]);
      scheduleAuto(id, durationMs);
      return id;
    },
    [scheduleAuto],
  );

  useEffect(
    () => () => {
      autoTimers.current.forEach((timer) => window.clearTimeout(timer));
      exitTimers.current.forEach((timer) => window.clearTimeout(timer));
      autoTimers.current.clear();
      exitTimers.current.clear();
    },
    [],
  );

  const controller = useMemo<ToastController>(() => ({ notify, dismiss }), [dismiss, notify]);

  return (
    <ToastContext.Provider value={controller}>
      {children}
      {items.length > 0 && (
        <div className="toast-viewport" data-ui="toast-viewport">
          {items.map((item) => (
            <div
              key={item.id}
              role={item.kind === "error" ? "alert" : "status"}
              aria-live={item.kind === "error" ? "assertive" : "polite"}
              aria-atomic="true"
              data-ui="toast"
              className={["toast", `toast-${item.kind}`, item.leaving && "is-leaving"]
                .filter(Boolean)
                .join(" ")}
              onMouseEnter={() => pause(item.id)}
              onMouseLeave={() => resume(item.id)}
              onFocus={() => pause(item.id)}
              onBlur={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
                  resume(item.id);
                }
              }}
            >
              <span className="toast-icon" aria-hidden="true">
                <ToastIcon kind={item.kind} />
              </span>
              <div className="toast-body">
                {item.title && <strong className="toast-title">{item.title}</strong>}
                <span>{item.message}</span>
              </div>
              <button
                type="button"
                className="toast-close"
                aria-label={t("toast.close")}
                onClick={() => dismiss(item.id)}
              >
                <IconX />
              </button>
            </div>
          ))}
        </div>
      )}
    </ToastContext.Provider>
  );
}
