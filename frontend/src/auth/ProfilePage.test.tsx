import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import type { ComponentProps } from "react";
import { I18nextProvider } from "react-i18next";

import { createClient } from "../api/client";
import type { ProfileData } from "../api/profile";
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
          <ProfilePage client={client} tokenStorage={storage} {...props} />
        </LiveAnnouncer>
      </I18nextProvider>,
    ),
  };
}

test("loads read-only email, preserves ZZ when unchanged, updates name and passes a11y", async () => {
  const patches: unknown[] = [];
  const updatedCallback = vi.fn();
  const initial: ProfileData = {
    email: "ana@empresa.com",
    name: "Usuario sin nombre",
    birthdate: "1991-03-04",
    country: "ZZ",
  };
  const fetcher: typeof fetch = (url, init) => {
    const path = String(url).split("?")[0];
    if (path.endsWith("/registration/options")) {
      return Promise.resolve(json(200, { countries: ["BR", "ES"], terms: null, marketing: null }));
    }
    if (init?.method === "PATCH") {
      const body = JSON.parse(String(init.body)) as Record<string, unknown>;
      patches.push(body);
      return Promise.resolve(json(200, { ...initial, name: "Ana Real" }));
    }
    return Promise.resolve(json(200, initial));
  };

  const user = userEvent.setup();
  renderProfile(fetcher, { onProfileUpdated: updatedCallback });
  const emailField = await screen.findByLabelText("Correo electrónico");
  expect(emailField).toHaveValue("ana@empresa.com");
  expect(emailField).toHaveAttribute("readonly");
  expect(screen.getByText("Sin país asignado")).toBeInTheDocument();

  const { violations } = await axe.run(document.body, {
    rules: { "color-contrast": { enabled: false } },
  });
  expect(violations).toEqual([]);

  const nameInput = screen.getByLabelText("Nombre completo");
  await user.clear(nameInput);
  await user.type(nameInput, "  Ana Real  ");
  await user.click(screen.getByRole("button", { name: "Guardar cambios" }));

  expect(await screen.findByText("Tus datos personales se han actualizado.")).toBeInTheDocument();
  expect(patches).toEqual([{ name: "  Ana Real  ", birthdate: "1991-03-04", language: "es" }]);
  expect(updatedCallback).toHaveBeenCalledWith({ email: "ana@empresa.com", name: "Ana Real" });
  expect(nameInput).toHaveValue("Ana Real");
});

test("validates required fields locally, focuses first error and displays server field errors", async () => {
  const fetcher: typeof fetch = (url, init) => {
    const path = String(url).split("?")[0];
    if (path.endsWith("/registration/options")) {
      return Promise.resolve(json(200, { countries: ["ES"], terms: null, marketing: null }));
    }
    if (init?.method === "PATCH") {
      return Promise.resolve(
        json(400, { errors: { name: [{ code: "name_consecutive_spaces", message: "x" }] } }),
      );
    }
    return Promise.resolve(
      json(200, {
        email: "eva@empresa.com",
        name: "Eva",
        birthdate: "1990-01-01",
        country: "ES",
      }),
    );
  };

  const user = userEvent.setup();
  renderProfile(fetcher);
  const nameInput = await screen.findByLabelText("Nombre completo");
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
});

test("redirects to /terms or /login when profile load or save fails auth gates", async () => {
  const onTerms = vi.fn();
  renderProfile(
    () => Promise.resolve(json(403, { code: "terms_required", terms_status: "not_accepted" })),
    { onTermsRequired: onTerms },
  );
  await waitFor(() => {
    expect(onTerms).toHaveBeenCalledWith("not_accepted");
    expect(window.location.pathname).toBe("/terms");
  });

  const onOut = vi.fn();
  const { storage } = renderProfile(() => Promise.resolve(json(401, { code: "unauthenticated" })), {
    onLoggedOut: onOut,
  });
  await waitFor(() => {
    expect(onOut).toHaveBeenCalled();
    expect(storage.get()).toBeNull();
    expect(window.location.pathname).toBe("/login");
  });
  window.history.replaceState(null, "", "/");
});
