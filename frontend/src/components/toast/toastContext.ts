import type { ParseKeys } from "i18next";
import { createContext, useContext } from "react";

export type ToastKind = "info" | "success" | "warning" | "error";

export type ToastInput = {
  kind?: ToastKind;
  title?: string;
  message?: string;
  messageKey?: ParseKeys;
  durationMs?: number;
};

export type ToastController = {
  notify: (input: ToastInput) => string;
  dismiss: (id: string, immediate?: boolean) => void;
};

export const DEFAULT_TOAST_DURATION_MS = 5000;

export const ToastContext = createContext<ToastController>({
  notify: () => "",
  dismiss: () => {},
});

export function useToast(): ToastController {
  return useContext(ToastContext);
}
