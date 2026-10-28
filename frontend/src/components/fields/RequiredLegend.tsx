import { useTranslation } from "react-i18next";

export function RequiredLegend() {
  const { t } = useTranslation();
  return <p>{t("field.requiredLegend")}</p>;
}
