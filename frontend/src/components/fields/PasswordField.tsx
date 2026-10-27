import { forwardRef, useRef, useState, type ComponentProps, type FocusEvent } from "react";
import { useTranslation } from "react-i18next";

import { TextField } from "./TextField";

type PasswordFieldProps = Omit<ComponentProps<typeof TextField>, "type" | "adornment"> & {
  kind: "current" | "new";
};

export const PasswordField = forwardRef<HTMLInputElement, PasswordFieldProps>(
  function PasswordField({ kind, onBlur, ...fieldProps }, ref) {
    const { t } = useTranslation();
    const [visible, setVisible] = useState(false);
    const inputRef = useRef<HTMLInputElement | null>(null);
    const toggleRef = useRef<HTMLButtonElement>(null);

    function setInput(node: HTMLInputElement | null) {
      inputRef.current = node;
      if (typeof ref === "function") ref(node);
      else if (ref) ref.current = node;
    }

    // El campo y su control cuentan como uno: solo se sale al dejar los dos (RF-025, D-16).
    function handleLeave(event: FocusEvent<HTMLElement>) {
      const input = inputRef.current;
      const next = event.relatedTarget;
      if (!input || next === input || next === toggleRef.current) return;
      onBlur?.(Object.create(event, { target: { value: input }, currentTarget: { value: input } }));
    }

    return (
      <TextField
        {...fieldProps}
        ref={setInput}
        type={visible ? "text" : "password"}
        autoComplete={kind === "current" ? "current-password" : "new-password"}
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        onBlur={handleLeave}
        adornment={
          <button
            ref={toggleRef}
            type="button"
            aria-pressed={visible}
            onClick={() => setVisible(!visible)}
            onBlur={handleLeave}
          >
            {t("field.showPassword")}
          </button>
        }
      />
    );
  },
);
