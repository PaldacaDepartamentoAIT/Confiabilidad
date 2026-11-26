import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import type { ComponentProps } from "react";
import { I18nextProvider } from "react-i18next";

import { createClient } from "../api/client";
import type { ProfileData } from "../api/profile";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { ToastProvider } from "../components/toast/ToastProvider";
import { createI18n } from "../i18n";
import { ProfilePage } from "./ProfilePage";
import { createTokenStorage } from "./tokenStorage";

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

const OK_OPTS = { countries: ["BR", "ES"], terms: null, marketing: null };

function renderProfile(
  fetcher: typeof fetch,
  props: Partial<ComponentProps<typeof ProfilePage>> = {},
) {
  Element.prototype.scrollIntoView = () => {};
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
          <ToastProvider>
            <ProfilePage client={client} tokenStorage={storage} {...props} />
          </ToastProvider>
        </LiveAnnouncer>
      </I18nextProvider>,
    ),
  };
}

test("starts in read-only mode with 3-dot menu, enters edit mode, preserves ZZ and passes a11y", async () => {
  const patches: unknown[] = [];
  const onProfileUpdated = vi.fn();
  const initial: ProfileData = {
    email: "ana@empresa.com",
    name: "Usuario sin nombre",
    birthdate: "1991-03-04",
    country: "ZZ",
  };
  let releaseProfile!: (res: Response) => void;

  const user = userEvent.setup();
  const { container } = renderProfile(
    (url, init) => {
      const path = String(url).split("?")[0];
      if (path.endsWith("/registration/options")) return Promise.resolve(json(200, OK_OPTS));
      if (init?.method === "PATCH") {
        patches.push(JSON.parse(String(init.body)));
        return Promise.resolve(json(200, { ...initial, name: "Ana Real" }));
      }
      return new Promise((resolve) => (releaseProfile = resolve));
    },
    { onProfileUpdated },
  );

  const section = screen.getByRole("region", { name: "Información personal" });
  expect(section).toHaveAttribute("aria-busy", "true");
  expect(section.querySelector(".skel-mask .lbl")).toHaveTextContent("Correo electrónico");
  expect(container.querySelectorAll(".is-loading .skeleton")).toHaveLength(4);

  releaseProfile(json(200, initial));

  const emailField = await screen.findByLabelText("Correo electrónico");
  expect(section).not.toHaveAttribute("aria-busy");
  expect(emailField).toHaveValue("ana@empresa.com");
  expect(emailField).toBeDisabled();
  expect([...section.querySelectorAll(".profile-grid label")].map((el) => el.textContent)).toEqual([
    "Nombre completo",
    "País",
    "Fecha de nacimiento",
  ]);
  expect(screen.getByLabelText("País")).toHaveValue("Sin país asignado");
  expect(screen.queryByRole("button", { name: "Guardar cambios" })).not.toBeInTheDocument();

  await user.click(screen.getByRole("combobox", { name: "Acciones del perfil" }));
  expect(screen.getByRole("option", { name: "Cambiar contraseña" })).toHaveAttribute(
    "aria-disabled",
    "true",
  );
  expect(screen.getByRole("option", { name: "Deshabilitar" })).toHaveAttribute(
    "aria-disabled",
    "true",
  );
  await user.click(screen.getByRole("option", { name: "Cambiar contraseña" }));
  expect(screen.getByRole("listbox", { name: "Acciones del perfil" })).toBeInTheDocument();

  await user.click(screen.getByRole("option", { name: "Editar" }));
  expect(
    (await axe.run(document.body, { rules: { "color-contrast": { enabled: false } } })).violations,
  ).toEqual([]);

  const nameInput = screen.getByLabelText("Nombre completo");
  await user.clear(nameInput);
  await user.type(nameInput, "  Ana Real  ");
  await user.click(screen.getByRole("button", { name: "Guardar cambios" }));

  const toast = await screen.findByRole("status");
  expect(toast).toHaveTextContent("Tus datos personales se han actualizado.");
  expect(section.contains(toast)).toBe(false);
  expect(screen.getByLabelText("Correo electrónico")).toBeDisabled();
  expect(patches).toEqual([{ name: "  Ana Real  ", birthdate: "1991-03-04", language: "es" }]);
  expect(onProfileUpdated).toHaveBeenCalledWith({ email: "ana@empresa.com", name: "Ana Real" });
  expect(screen.getByLabelText("Nombre completo")).toHaveValue("Ana Real");
  expect(screen.getByLabelText("Nombre completo")).toHaveAttribute("readonly");
});

test("validates fields in edit mode, focuses first error, shows server error and supports cancel", async () => {
  const user = userEvent.setup();
  renderProfile((url, init) => {
    const path = String(url).split("?")[0];
    if (path.endsWith("/registration/options")) return Promise.resolve(json(200, OK_OPTS));
    if (init?.method === "PATCH") {
      return Promise.resolve(
        json(400, { errors: { name: [{ code: "name_consecutive_spaces", message: "x" }] } }),
      );
    }
    return Promise.resolve(
      json(200, { email: "eva@empresa.com", name: "Eva", birthdate: "1990-01-01", country: "ES" }),
    );
  });

  await screen.findByLabelText("Correo electrónico");
  await user.click(screen.getByRole("combobox", { name: "Acciones del perfil" }));
  await user.click(screen.getByRole("option", { name: "Editar" }));

  const nameInput = screen.getByLabelText("Nombre completo");
  await user.clear(nameInput);
  await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
  expect(screen.getByText("Completa este campo.")).toBeInTheDocument();
  expect(nameInput).toHaveFocus();

  await user.type(nameInput, "Eva  Ruiz");
  await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
  expect(
    await screen.findByText("El nombre no puede tener espacios seguidos."),
  ).toBeInTheDocument();
  expect(nameInput).toHaveFocus();

  await user.click(screen.getByRole("button", { name: "Cancelar" }));
  expect(screen.queryByRole("button", { name: "Guardar cambios" })).not.toBeInTheDocument();
  expect(screen.getByLabelText("Nombre completo")).toHaveValue("Eva");
});

test("redirects to /terms or /login when profile fails auth or terms gates", async () => {
  const onTerms = vi.fn();
  renderProfile(
    (url) =>
      Promise.resolve(
        String(url).includes("/options")
          ? json(200, OK_OPTS)
          : json(403, { code: "terms_required", terms_status: "not_accepted" }),
      ),
    { onTermsRequired: onTerms },
  );
  await waitFor(() => expect(window.location.pathname).toBe("/terms"));
  expect(onTerms).toHaveBeenCalledWith("not_accepted");

  const onOut = vi.fn();
  const { storage } = renderProfile(
    (url) =>
      Promise.resolve(
        String(url).includes("/options")
          ? json(200, OK_OPTS)
          : json(401, { code: "unauthenticated" }),
      ),
    { onLoggedOut: onOut },
  );
  await waitFor(() => expect(window.location.pathname).toBe("/login"));
  expect(onOut).toHaveBeenCalled();
  expect(storage.get()).toBeNull();
  window.history.replaceState(null, "", "/");
});
