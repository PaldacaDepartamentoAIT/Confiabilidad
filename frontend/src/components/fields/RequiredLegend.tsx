import { useTranslation } from "react-i18next";

import "./field.css";

export function RequiredLegend() {
  const { t } = useTranslation();
  return <p className="help">{t("field.requiredLegend")}</p>;
}
