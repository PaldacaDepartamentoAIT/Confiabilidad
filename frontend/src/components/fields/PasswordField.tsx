import { forwardRef, useState, type ComponentProps } from "react";
import { useTranslation } from "react-i18next";

import { TextField } from "./TextField";

type PasswordFieldProps = Omit<ComponentProps<typeof TextField>, "type" | "adornment"> & {
  kind: "current" | "new";
};

export const PasswordField = forwardRef<HTMLInputElement, PasswordFieldProps>(
  function PasswordField({ kind, ...fieldProps }, ref) {
    const { t } = useTranslation();
    const [visible, setVisible] = useState(false);

    return (
      <TextField
        {...fieldProps}
        ref={ref}
        type={visible ? "text" : "password"}
        autoComplete={kind === "current" ? "current-password" : "new-password"}
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        adornment={
          <button type="button" aria-pressed={visible} onClick={() => setVisible(!visible)}>
            {t("field.showPassword")}
          </button>
        }
      />
    );
  },
);
