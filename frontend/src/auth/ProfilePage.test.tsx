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
  language = "es",
) {
  Element.prototype.scrollIntoView = () => {};
  const i18n = createI18n(language);
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
  expect(screen.getByRole("option", { name: "Cambiar contraseña" })).not.toHaveAttribute(
    "aria-disabled",
  );
  expect(screen.getByRole("option", { name: "Deshabilitar" })).toHaveAttribute(
    "aria-disabled",
    "true",
  );
  await user.click(screen.getByRole("option", { name: "Deshabilitar" }));
  expect(screen.getByRole("listbox", { name: "Acciones del perfil" })).toBeInTheDocument();

  await user.click(screen.getByRole("option", { name: "Editar" }));
  expect(
    (await axe.run(document.body, { rules: { "color-contrast": { enabled: false } } })).violations,
  ).toEqual([]);

  const nameInput = screen.getByRole("textbox", { name: "Nombre completo" });
  await user.clear(nameInput);
  await user.type(nameInput, "  Ana Real  ");
  await user.click(screen.getByRole("button", { name: "Guardar cambios" }));

  const toastMessage = await screen.findByText("Tus datos personales se han actualizado.");
  const toast = toastMessage.closest('[data-ui="toast"]');
  expect(toast).toHaveAttribute("role", "status");
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

  const nameInput = screen.getByRole("textbox", { name: "Nombre completo" });
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

test("switches to password change from menu, validates, clears selectively, shows toast and passes a11y", async () => {
  const user = userEvent.setup();
  const replies = [
    json(400, {
      errors: { current_password: [{ code: "current_password_incorrect", message: "x" }] },
    }),
    json(400, { errors: { new_password: [{ code: "password_too_common", message: "x" }] } }),
    json(200, { result: "password_changed" }),
  ];
  const sent: unknown[] = [];
  renderProfile((url, init) => {
    const path = String(url).split("?")[0];
    if (path.endsWith("/registration/options")) return Promise.resolve(json(200, OK_OPTS));
    if (path.endsWith("/password/change")) {
      sent.push(JSON.parse(String(init?.body)));
      return Promise.resolve(replies.shift()!);
    }
    return Promise.resolve(
      json(200, { email: "ana@empresa.com", name: "Ana", birthdate: "1991-03-04", country: "ES" }),
    );
  });

  await screen.findByLabelText("Correo electrónico");
  await user.click(screen.getByRole("combobox", { name: "Acciones del perfil" }));
  await user.click(screen.getByRole("option", { name: "Cambiar contraseña" }));
  expect(screen.getByRole("heading", { level: 2, name: "Cambiar contraseña" })).toBeInTheDocument();
  expect(
    (await axe.run(document.body, { rules: { "color-contrast": { enabled: false } } })).violations,
  ).toEqual([]);

  const curInput = screen.getByLabelText(/^Contraseña actual/);
  const newInput = screen.getByLabelText(/^Nueva contraseña/);
  expect(newInput).toHaveAccessibleDescription(
    expect.stringContaining("Al menos 12 caracteres") as string,
  );
  await user.click(screen.getByRole("button", { name: "Mostrar contraseña (Nueva contraseña)" }));
  expect(newInput).toHaveAttribute("type", "text");

  await user.type(curInput, "clave-actual-1");
  await user.type(newInput, "corta");
  await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
  expect(newInput).toHaveAccessibleDescription(
    expect.stringContaining("Usa al menos 12 caracteres.") as string,
  );
  expect(sent).toEqual([]);

  await user.clear(newInput);
  await user.type(newInput, "turbina-nueva-99");
  await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
  expect(await screen.findByText("La contraseña actual no es correcta.")).toBeInTheDocument();
  expect(curInput).toHaveFocus();
  expect(curInput).toHaveValue("");
  expect(newInput).toHaveValue("turbina-nueva-99");

  await user.type(curInput, "clave-correcta-1");
  await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
  expect(await screen.findByText("Esta contraseña es demasiado común.")).toBeInTheDocument();
  expect(newInput).toHaveFocus();
  expect(curInput).toHaveValue("clave-correcta-1");
  expect(newInput).toHaveValue("turbina-nueva-99");

  await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
  expect(
    (
      await screen.findByText(
        "Tu contraseña se ha actualizado y se han cerrado tus demás sesiones.",
      )
    ).closest('[data-ui="toast"]'),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("heading", { level: 2, name: "Información personal" }),
  ).toBeInTheDocument();
  expect(sent).toHaveLength(3);
});

test("handles 429 countdown, network failures, cancel, i18n and gate redirects on password change", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const onTerms = vi.fn();
  try {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const answers = [
      () => Promise.reject(new TypeError("Failed to fetch")),
      () => Promise.resolve(json(429, { retry_after: 2 })),
      () => Promise.resolve(json(403, { code: "terms_required", terms_status: "not_accepted" })),
    ];
    renderProfile(
      (url) => {
        const path = String(url).split("?")[0];
        if (path.endsWith("/registration/options")) return Promise.resolve(json(200, OK_OPTS));
        if (path.endsWith("/password/change")) return answers.shift()!();
        return Promise.resolve(
          json(200, {
            email: "ana@empresa.com",
            name: "Ana",
            birthdate: "1991-03-04",
            country: "ES",
          }),
        );
      },
      { onTermsRequired: onTerms },
      "en",
    );

    await screen.findByLabelText("Email");
    await user.click(screen.getByRole("combobox", { name: "Profile actions" }));
    await user.click(screen.getByRole("option", { name: "Change password" }));

    await user.type(screen.getByLabelText(/^Current password/), "draft-secret");
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(
      screen.getByRole("heading", { level: 2, name: "Personal information" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("combobox", { name: "Profile actions" }));
    await user.click(screen.getByRole("option", { name: "Change password" }));

    const cur = screen.getByLabelText(/^Current password/);
    expect(cur).toHaveValue("");
    const next = screen.getByLabelText(/^New password/);
    await user.type(cur, "old-secret-1");
    await user.type(next, "new-turbine-123");
    await user.click(screen.getByRole("button", { name: "Change password" }));
    expect(await screen.findByText(/Could not connect/)).toHaveFocus();
    expect(cur).toHaveValue("old-secret-1");
    expect(next).toHaveValue("new-turbine-123");

    await user.click(screen.getByRole("button", { name: "Change password" }));
    expect(await screen.findByText("Too many attempts. Try again in 2 s.")).toBeInTheDocument();
    const submit = screen.getByRole("button", { name: "Change password" });
    expect(submit).toBeDisabled();
    await act(() => vi.advanceTimersByTimeAsync(2000));
    expect(submit).toBeEnabled();

    await user.click(submit);
    await waitFor(() => expect(window.location.pathname).toBe("/terms"));
    expect(onTerms).toHaveBeenCalledWith("not_accepted");
  } finally {
    vi.useRealTimers();
    window.history.replaceState(null, "", "/");
  }
});
