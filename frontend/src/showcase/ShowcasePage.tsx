import { useId } from "react";
import { useTranslation } from "react-i18next";

import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { RequiredLegend } from "../components/fields/RequiredLegend";
import { TextField } from "../components/fields/TextField";
import type { LanguageStorage } from "../i18n/language";

type ShowcasePageProps = {
  storage?: LanguageStorage;
};

export function ShowcasePage({ storage }: ShowcasePageProps) {
  const { t } = useTranslation();
  const formTitleId = useId();

  return (
    <main>
      <LanguageSwitcher storage={storage} />
      <h1>{t("app.heading")}</h1>
      <p>{t("app.intro")}</p>
      <h2 id={formTitleId}>{t("showcase.formTitle")}</h2>
      <RequiredLegend />
      <form aria-labelledby={formTitleId} noValidate>
        <TextField label={t("showcase.nameLabel")} name="name" autoComplete="name" required />
        <TextField label={t("showcase.emailLabel")} name="email" type="email" required />
      </form>
    </main>
  );
}
