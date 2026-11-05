import { useTranslation } from "react-i18next";

import { THEMES, useTheme, type ThemeStorage } from "../theme/theme";
import { MoonIcon, SunIcon } from "./icons";
import { MenuButton } from "./MenuButton";

type ThemeMenuProps = {
  storage?: ThemeStorage;
};

export function ThemeMenu({ storage }: ThemeMenuProps) {
  const { t } = useTranslation();
  const { theme, choose } = useTheme(storage);
  const options = THEMES.map((value) => ({ value, label: t(`topBar.${value}`) }));

  return (
    <MenuButton
      label={t("topBar.theme", { name: t(`topBar.${theme}`) })}
      menuLabel={t("topBar.themeLabel")}
      options={options}
      value={theme}
      onSelect={choose}
    >
      {theme === "dark" ? <MoonIcon /> : <SunIcon />}
    </MenuButton>
  );
}
