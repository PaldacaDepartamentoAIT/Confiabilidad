import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAnnouncer } from "../components/announcer";
import "./ThemeButton.css";
import { getTheme, toggleTheme, type Theme, type ThemeStorage } from "./theme";

type ThemeButtonProps = {
  storage?: ThemeStorage;
};

// Iconos de lucide (sol y luna) dibujados aquí hasta que exista el módulo de iconos (T-006).
function ThemeIcon({ theme }: { theme: Theme }) {
  return (
    <svg
      className="i"
      data-icon={theme === "dark" ? "moon" : "sun"}
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
    >
      {theme === "dark" ? (
        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
      ) : (
        <>
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M2 12h2M20 12h2" />
          <path d="m4.93 4.93 1.41 1.41M17.66 17.66l1.41 1.41M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
        </>
      )}
    </svg>
  );
}

export function ThemeButton({ storage }: ThemeButtonProps) {
  const { t } = useTranslation();
  const announce = useAnnouncer();
  const [theme, setTheme] = useState<Theme>(() => getTheme());
  const announcement = (value: Theme) =>
    value === "dark" ? t("theme.announceDark") : t("theme.announceLight");

  function toggle() {
    const next = toggleTheme({ storage });
    setTheme(next);
    announce(announcement(next), "polite");
  }

  return (
    <button
      type="button"
      className="sb-btn hov"
      data-ui="sidebar-button"
      aria-label={`${announcement(theme)}. ${t("theme.toggle")}`}
      onClick={toggle}
    >
      <ThemeIcon theme={theme} />
      <span className="label">{theme === "dark" ? t("theme.dark") : t("theme.light")}</span>
    </button>
  );
}
