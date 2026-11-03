import { useEffect, useState, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";

import type { ApiClient } from "../api/client";
import { fetchOptions, fetchStatus } from "../api/registration";
import { FormMessage } from "../components/FormMessage";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import type { LanguageStorage } from "../i18n/language";
import { navigate, useLocation } from "../routing/router";
import { useCountdown } from "./useCountdown";

type Loaded = "loading" | "ready" | "notFound" | "networkError" | "failed";

function hasCsrfCookie(): boolean {
  return document.cookie.split(";").some((part) => part.trim().startsWith("csrftoken="));
}

function minutesAndSeconds(total: number): string {
  const seconds = String(total % 60).padStart(2, "0");
  return `${Math.floor(total / 60)}:${seconds}`;
}

type VerifyPageProps = {
  client: ApiClient;
  storage?: LanguageStorage;
};

export function VerifyPage({ client, storage }: VerifyPageProps) {
  const { t } = useTranslation();
  const publicId = useLocation().hash;
  const [loaded, setLoaded] = useState<Loaded>(publicId ? "loading" : "notFound");
  const expiry = useCountdown();
  const { start } = expiry;

  useEffect(() => {
    if (!publicId) return;
    let current = true;
    async function load() {
      // El enlace del correo puede abrirse en un navegador sin la cookie CSRF que piden los POST (D-09).
      if (!hasCsrfCookie()) await fetchOptions(client);
      const result = await fetchStatus(client, publicId);
      if (!current) return;
      if (result.kind === "ok") {
        start(result.data.code_expires_in);
        setLoaded("ready");
      } else if (result.kind === "notFound") setLoaded("notFound");
      else if (result.kind === "networkError") setLoaded("networkError");
      else setLoaded("failed");
    }
    void load();
    return () => {
      current = false;
    };
  }, [client, publicId, start]);

  if (loaded === "notFound") return <InvalidLink storage={storage} />;

  return (
    <main>
      <LanguageSwitcher storage={storage} />
      <h1>{t("register.verifyTitle")}</h1>
      <p>{t("register.verifyText")}</p>
      {loaded === "networkError" && (
        <FormMessage type="error" messageKey="validation.networkError" />
      )}
      {loaded === "failed" && <FormMessage type="error" messageKey="validation.serverError" />}
      {loaded === "ready" && (
        <p>
          {expiry.remaining > 0
            ? t("register.codeExpiresIn", { time: minutesAndSeconds(expiry.remaining) })
            : t("register.codeExpiredNotice")}
        </p>
      )}
    </main>
  );
}

function InvalidLink({ storage }: { storage?: LanguageStorage }) {
  const { t } = useTranslation();

  function goToForm(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    navigate("/register");
  }

  return (
    <main>
      <LanguageSwitcher storage={storage} />
      <h1>{t("register.invalidLinkTitle")}</h1>
      <p>{t("validation.linkNotFound")}</p>
      <a href="/register" onClick={goToForm}>
        {t("register.backToForm")}
      </a>
    </main>
  );
}
