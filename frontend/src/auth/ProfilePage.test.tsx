import { render, screen, waitFor } from "@testing-library/react";
import axe from "axe-core";
import type { ComponentProps } from "react";
import { I18nextProvider } from "react-i18next";

import { createClient } from "../api/client";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { createI18n } from "../i18n";
import { ProfilePage } from "./ProfilePage";
import { createTokenStorage } from "./tokenStorage";

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

function renderProfile(
  fetcher: typeof fetch,
  props: Partial<ComponentProps<typeof ProfilePage>> = {},
) {
  const i18n = createI18n("es");
  const storage = createTokenStorage(null);
  storage.set("tok-profile");
  const client = createClient({
    kind: "app",
    appBaseUrl: "",
    language: () => i18n.language,
    fetch: fetcher,
    tokenStorage: storage,
  });
  return {
    storage,
    ...render(
      <I18nextProvider i18n={i18n}>
        <LiveAnnouncer>
          <ProfilePage client={client} tokenStorage={storage} {...props} />
        </LiveAnnouncer>
      </I18nextProvider>,
    ),
  };
}

test("renders skeleton placeholders while loading, shows ZZ placeholder and passes a11y", async () => {
  let resolveFetch!: (res: Response) => void;
  const { container } = renderProfile(() => new Promise((resolve) => (resolveFetch = resolve)));

  const section = screen.getByRole("region", { name: "Información personal" });
  expect(section).toHaveAttribute("aria-busy", "true");
  expect(section.querySelector(".skel-mask .lbl")).toHaveTextContent("Correo electrónico");
  expect(container.querySelectorAll(".is-loading .skeleton")).toHaveLength(4);

  resolveFetch(
    json(200, {
      email: "ana@empresa.com",
      name: "Ana Real",
      birthdate: "1991-03-04",
      country: "ZZ",
    }),
  );

  const emailField = await screen.findByLabelText("Correo electrónico");
  expect(section).toHaveAttribute("aria-busy", "false");
  expect(container.querySelectorAll(".is-loading")).toHaveLength(0);
  expect(container.querySelectorAll(".is-ready")).toHaveLength(4);
  expect(emailField).toHaveValue("ana@empresa.com");
  expect(emailField).toHaveAttribute("readonly");
  expect(screen.getByLabelText("Nombre completo")).toHaveValue("Ana Real");
  expect(screen.getByLabelText("Fecha de nacimiento")).toHaveValue("1991-03-04");
  expect(screen.getByLabelText("País")).toHaveValue("Sin país asignado");
  expect(
    (await axe.run(document.body, { rules: { "color-contrast": { enabled: false } } })).violations,
  ).toEqual([]);
});

test("redirects to /terms or /login when profile fails auth or terms gates", async () => {
  const onTerms = vi.fn();
  renderProfile(
    () => Promise.resolve(json(403, { code: "terms_required", terms_status: "not_accepted" })),
    { onTermsRequired: onTerms },
  );
  await waitFor(() => expect(window.location.pathname).toBe("/terms"));
  expect(onTerms).toHaveBeenCalledWith("not_accepted");

  const onOut = vi.fn();
  const { storage } = renderProfile(() => Promise.resolve(json(401, { code: "unauthenticated" })), {
    onLoggedOut: onOut,
  });
  await waitFor(() => expect(window.location.pathname).toBe("/login"));
  expect(onOut).toHaveBeenCalled();
  expect(storage.get()).toBeNull();
  window.history.replaceState(null, "", "/");
});
