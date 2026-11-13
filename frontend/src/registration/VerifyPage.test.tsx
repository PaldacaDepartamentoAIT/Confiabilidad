import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { createClient } from "../api/client";
import type { RegistrationStatus } from "../api/registration";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { createI18n } from "../i18n";
import { DonePage } from "./DonePage";
import { VerifyPage } from "./VerifyPage";

const STATUS: RegistrationStatus = {
  code_expires_in: 900,
  resend_in: 60,
  resends_left: 5,
  locked: false,
  expired: false,
};

type Call = { method: string; url: string; body?: unknown };

function replies(...responses: (() => Promise<Response>)[]) {
  const calls: Call[] = [];
  const fetcher = (url: RequestInfo | URL, init?: RequestInit) => {
    const body = init?.body ? (JSON.parse(String(init.body)) as unknown) : undefined;
    calls.push({ method: init?.method ?? "GET", url: String(url), body });
    const next = responses.shift();
    return next ? next() : Promise.reject(new Error("unexpected call"));
  };
  return { calls, fetcher: fetcher as typeof fetch };
}

const reply = (status: number, body: unknown) => () =>
  Promise.resolve(new Response(JSON.stringify(body), { status }));

function renderPage(fetcher: typeof fetch) {
  const i18n = createI18n("es");
  const client = createClient({
    kind: "browser",
    appBaseUrl: "",
    language: () => i18n.language,
    fetch: fetcher,
  });
  return render(
    <I18nextProvider i18n={i18n}>
      <LiveAnnouncer>
        <VerifyPage client={client} />
      </LiveAnnouncer>
    </I18nextProvider>,
  );
}

function openAt(url: string, withCsrfCookie = true) {
  window.history.pushState(null, "", url);
  document.cookie = withCsrfCookie
    ? "csrftoken=token"
    : "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
}

afterEach(() => {
  vi.useRealTimers();
  window.history.pushState(null, "", "/");
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
});

test("asks for the status of the identifier in the fragment and shows the fixed text", async () => {
  openAt("/register/continue#pid-1");
  const { calls, fetcher } = replies(reply(200, STATUS));
  const { container } = renderPage(fetcher);

  expect(await screen.findByText("El código caduca en 15:00.")).toBeInTheDocument();
  expect(calls).toEqual([
    {
      method: "POST",
      url: "/api/browser/v1/registration/status",
      body: { public_id: "pid-1", language: "es" },
    },
  ]);
  expect(
    screen.getByRole("heading", { level: 1, name: "Escribe el código de verificación" }),
  ).toBeInTheDocument();
  expect(screen.getByText(/^Si puedes registrarte con el correo que escribiste/)).toBeVisible();
  expect(container.textContent).not.toContain("@");
});

test("the remaining time counts down and says when the code has expired", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  openAt("/register/continue#pid-1");
  const { fetcher } = replies(reply(200, { ...STATUS, code_expires_in: 61 }));
  renderPage(fetcher);

  await screen.findByText("El código caduca en 1:01.");
  await act(() => vi.advanceTimersByTimeAsync(2000));
  expect(screen.getByText("El código caduca en 0:59.")).toBeInTheDocument();

  await act(() => vi.advanceTimersByTimeAsync(59_000));
  expect(screen.getByText("El código ha caducado. Pide uno nuevo.")).toBeInTheDocument();
  expect(screen.queryByText(/^El código caduca en/)).toBeNull();
});

test("an expired code from the server is shown as expired", async () => {
  openAt("/register/continue#pid-1");
  const { fetcher } = replies(reply(200, { ...STATUS, code_expires_in: 0, expired: true }));
  renderPage(fetcher);

  expect(await screen.findByText("El código ha caducado. Pide uno nuevo.")).toBeInTheDocument();
});

test("without the CSRF cookie, asks for it before the first POST", async () => {
  openAt("/register/continue#pid-1", false);
  const { calls, fetcher } = replies(
    reply(200, { countries: [], terms: null, marketing: null }),
    reply(200, STATUS),
  );
  renderPage(fetcher);

  await screen.findByText("El código caduca en 15:00.");
  expect(calls.map((call) => `${call.method} ${call.url}`)).toEqual([
    "GET /api/browser/v1/registration/options?language=es",
    "POST /api/browser/v1/registration/status",
  ]);
});

test("reloading asks the server again", async () => {
  openAt("/register/continue#pid-1");
  const { calls, fetcher } = replies(
    reply(200, STATUS),
    reply(200, { ...STATUS, code_expires_in: 30 }),
  );
  const { unmount } = renderPage(fetcher);
  await screen.findByText("El código caduca en 15:00.");
  unmount();

  renderPage(fetcher);

  expect(await screen.findByText("El código caduca en 0:30.")).toBeInTheDocument();
  expect(calls).toHaveLength(2);
});

test("an unknown identifier shows the invalid link with access to the form", async () => {
  const user = userEvent.setup();
  openAt("/register/continue#unknown");
  const { fetcher } = replies(reply(404, { code: "not_found", message: "x" }));
  renderPage(fetcher);

  expect(await screen.findByRole("heading", { level: 1, name: "Enlace no válido" })).toBeVisible();
  expect(screen.getByText("El enlace no es válido o ha caducado.")).toBeVisible();
  await user.click(screen.getByRole("link", { name: "Ir al formulario de registro" }));
  expect(window.location.pathname).toBe("/register");
});

test("without an identifier, the link is not valid and nothing is asked", async () => {
  openAt("/register/continue");
  const { calls, fetcher } = replies();
  renderPage(fetcher);

  expect(await screen.findByRole("heading", { level: 1, name: "Enlace no válido" })).toBeVisible();
  expect(calls).toEqual([]);
});

test.each([
  [() => Promise.reject(new TypeError("Failed to fetch")), /No se pudo conectar/],
  [reply(500, {}), /Algo falló en nuestro servidor/],
])("if the status cannot be asked, says so", async (failure, text) => {
  openAt("/register/continue#pid-1");
  const { fetcher } = replies(failure);
  renderPage(fetcher);

  expect(await screen.findByText(text)).toBeInTheDocument();
});

test("if the identifier changes, a late answer for the old one is ignored", async () => {
  openAt("/register/continue#old");
  let answerOld: (response: Response) => void = () => {};
  const { fetcher } = replies(
    () => new Promise<Response>((resolve) => (answerOld = resolve)),
    reply(200, { ...STATUS, code_expires_in: 30 }),
  );
  renderPage(fetcher);

  act(() => {
    window.history.pushState(null, "", "/register/continue#new");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await screen.findByText("El código caduca en 0:30.");
  await act(async () => {
    answerOld(new Response(JSON.stringify(STATUS), { status: 200 }));
    await Promise.resolve();
  });

  expect(screen.getByText("El código caduca en 0:30.")).toBeInTheDocument();
});

async function typeCode(user: ReturnType<typeof userEvent.setup>, code: string) {
  await user.type(await screen.findByRole("textbox", { name: "Código de verificación" }), code);
  await user.click(screen.getByRole("button", { name: "Verificar" }));
}

describe("verifying the code", () => {
  it("a wrong code shows its message under the field", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { calls, fetcher } = replies(
      reply(200, STATUS),
      reply(400, { code: "wrong_code", message: "x" }),
    );
    renderPage(fetcher);

    await typeCode(user, "123456");

    const field = screen.getByRole("textbox", { name: "Código de verificación" });
    await waitFor(() =>
      expect(field).toHaveAccessibleDescription(
        "El código no es correcto. Revísalo e inténtalo de nuevo.",
      ),
    );
    expect(calls[1]).toEqual({
      method: "POST",
      url: "/api/browser/v1/registration/verify",
      body: { public_id: "pid-1", code: "123456", language: "es" },
    });
  });

  it("an expired code asks for another one under the field", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { calls, fetcher } = replies(
      reply(200, STATUS),
      reply(400, { code: "code_expired", message: "x" }),
    );
    renderPage(fetcher);

    await typeCode(user, "123456");

    await waitFor(() =>
      expect(
        screen.getByRole("textbox", { name: "Código de verificación" }),
      ).toHaveAccessibleDescription("El código ha caducado. Pide uno nuevo."),
    );
    expect(calls).toHaveLength(2);
  });

  it("an incomplete code is not sent", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { calls, fetcher } = replies(reply(200, STATUS));
    renderPage(fetcher);

    await typeCode(user, "123");

    expect(
      screen.getByRole("textbox", { name: "Código de verificación" }),
    ).toHaveAccessibleDescription("Escribe los 6 dígitos del código.");
    expect(calls).toHaveLength(1);
  });

  it("when the attempts run out, the sending is disabled", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(reply(200, STATUS), reply(400, { code: "locked", message: "x" }));
    renderPage(fetcher);

    await typeCode(user, "123456");

    expect(
      await screen.findByText(
        "Has agotado los intentos con este código. Pide uno nuevo para continuar.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verificar" })).toBeDisabled();
  });

  it("the fifth wrong code shows the lock without another attempt", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { calls, fetcher } = replies(
      reply(200, STATUS),
      reply(400, { code: "wrong_code", message: "x" }),
      reply(200, { ...STATUS, locked: true }),
    );
    renderPage(fetcher);

    await typeCode(user, "123456");

    expect(await screen.findByText(/^Has agotado los intentos/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verificar" })).toBeDisabled();
    expect(calls.map((call) => call.url.split("/").pop())).toEqual(["status", "verify", "status"]);
  });

  it("if the identifier disappears after a wrong code, the link is not valid", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(
      reply(200, STATUS),
      reply(400, { code: "wrong_code", message: "x" }),
      reply(404, { code: "not_found", message: "x" }),
    );
    renderPage(fetcher);

    await typeCode(user, "123456");

    expect(
      await screen.findByRole("heading", { level: 1, name: "Enlace no válido" }),
    ).toBeVisible();
  });

  it("a wrong code that does not lock keeps its message under the field", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { calls, fetcher } = replies(
      reply(200, STATUS),
      reply(400, { code: "wrong_code", message: "x" }),
      reply(200, STATUS),
    );
    renderPage(fetcher);

    await typeCode(user, "123456");

    await waitFor(() => expect(calls).toHaveLength(3));
    expect(
      screen.getByRole("textbox", { name: "Código de verificación" }),
    ).toHaveAccessibleDescription("El código no es correcto. Revísalo e inténtalo de nuevo.");
    expect(screen.getByRole("button", { name: "Verificar" })).toBeEnabled();
    expect(screen.queryByText(/^Has agotado los intentos/)).toBeNull();
  });

  it("a locked process stays locked after reloading", async () => {
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(reply(200, { ...STATUS, locked: true }));
    renderPage(fetcher);

    expect(await screen.findByText(/^Has agotado los intentos/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verificar" })).toBeDisabled();
  });

  it("over the limit, counts down and allows sending again at zero", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(reply(200, STATUS), reply(429, { message: "x", retry_after: 3 }));
    renderPage(fetcher);

    await typeCode(user, "123456");

    expect(
      await screen.findByText("Demasiados intentos. Vuelve a intentarlo en 3 s."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verificar" })).toBeDisabled();
    await act(() => vi.advanceTimersByTimeAsync(3000));
    expect(screen.getByRole("button", { name: "Verificar" })).toBeEnabled();
    expect(screen.getByRole("textbox", { name: "Código de verificación" })).toHaveValue("123456");
  });

  it.each([
    [reply(400, { code: "expired", message: "x" }), /El registro ha caducado/],
    [() => Promise.reject(new TypeError("Failed to fetch")), /No se pudo conectar/],
    [reply(500, {}), /Algo falló en nuestro servidor/],
  ])("any other answer gives a general message", async (answer, text) => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(reply(200, STATUS), answer);
    renderPage(fetcher);

    await typeCode(user, "123456");

    expect(await screen.findByText(text)).toHaveFocus();
  });

  it("an identifier that disappears while verifying shows the invalid link", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(
      reply(200, STATUS),
      reply(404, { code: "not_found", message: "x" }),
    );
    renderPage(fetcher);

    await typeCode(user, "123456");

    expect(
      await screen.findByRole("heading", { level: 1, name: "Enlace no válido" }),
    ).toBeVisible();
  });
});

describe("sending another code", () => {
  it("the button counts down, says how many are left and turns on at zero", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(reply(200, { ...STATUS, resend_in: 2, resends_left: 3 }));
    renderPage(fetcher);

    expect(await screen.findByRole("button", { name: "Enviar otro código en 2 s" })).toBeDisabled();
    expect(screen.getByText("Códigos que aún puedes pedir: 3.")).toBeInTheDocument();
    await act(() => vi.advanceTimersByTimeAsync(2000));
    expect(screen.getByRole("button", { name: "Enviar otro código" })).toBeEnabled();
  });

  it("after sending, asks for the status again and lifts the lock", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { calls, fetcher } = replies(
      reply(200, { ...STATUS, resend_in: 0, locked: true }),
      reply(202, { result: "resent" }),
      reply(200, { ...STATUS, resends_left: 4 }),
    );
    renderPage(fetcher);

    await user.click(await screen.findByRole("button", { name: "Enviar otro código" }));

    expect(await screen.findByText("Códigos que aún puedes pedir: 4.")).toBeInTheDocument();
    expect(
      screen.getByText(/Si puedes registrarte, recibirás un código nuevo/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verificar" })).toBeEnabled();
    expect(calls.map((call) => call.url.split("/").pop())).toEqual(["status", "resend", "status"]);
    expect(calls[1].body).toEqual({ public_id: "pid-1", language: "es" });
  });

  it("without codes left, the button is off and the form is offered", async () => {
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(reply(200, { ...STATUS, resend_in: 0, resends_left: 0 }));
    renderPage(fetcher);

    expect(await screen.findByRole("button", { name: "Enviar otro código" })).toBeDisabled();
    expect(
      screen.getByText("No puedes pedir más códigos. Vuelve a empezar el registro."),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ir al formulario de registro" })).toBeVisible();
  });

  it("an identifier that disappears while sending shows the invalid link", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(
      reply(200, { ...STATUS, resend_in: 0 }),
      reply(404, { code: "not_found", message: "x" }),
    );
    renderPage(fetcher);

    await user.click(await screen.findByRole("button", { name: "Enviar otro código" }));

    expect(
      await screen.findByRole("heading", { level: 1, name: "Enlace no válido" }),
    ).toBeVisible();
  });

  it("a new attempt removes the message of the previous one", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(
      reply(200, { ...STATUS, resend_in: 0 }),
      reply(500, {}),
      reply(429, { message: "x", retry_after: 5 }),
    );
    renderPage(fetcher);

    await user.click(await screen.findByRole("button", { name: "Enviar otro código" }));
    await screen.findByText(/Algo falló en nuestro servidor/);
    await user.click(screen.getByRole("button", { name: "Enviar otro código" }));

    await screen.findByRole("button", { name: "Enviar otro código en 5 s" });
    expect(screen.queryByText(/Algo falló en nuestro servidor/)).toBeNull();
  });

  it("over the limit, says so with the wait and allows sending again at zero", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(
      reply(200, { ...STATUS, resend_in: 0 }),
      reply(429, { message: "x", retry_after: 5 }),
    );
    renderPage(fetcher);

    await user.click(await screen.findByRole("button", { name: "Enviar otro código" }));

    expect(await screen.findByRole("button", { name: "Enviar otro código en 5 s" })).toBeDisabled();
    expect(screen.getByText("Demasiados intentos. Vuelve a intentarlo en 5 s.")).toHaveAttribute(
      "role",
      "status",
    );
    await act(() => vi.advanceTimersByTimeAsync(5000));
    expect(screen.getByRole("button", { name: "Enviar otro código" })).toBeEnabled();
    expect(screen.queryByText(/Demasiados intentos/)).toBeNull();
  });

  it("after the limit, the normal wait of a new code is not announced as a limit", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(
      reply(200, { ...STATUS, resend_in: 0 }),
      reply(429, { message: "x", retry_after: 1 }),
      reply(202, { result: "resent" }),
      reply(200, STATUS),
    );
    renderPage(fetcher);
    await user.click(await screen.findByRole("button", { name: "Enviar otro código" }));
    await screen.findByText(/Demasiados intentos/);
    await act(() => vi.advanceTimersByTimeAsync(1000));

    await user.click(screen.getByRole("button", { name: "Enviar otro código" }));

    expect(
      await screen.findByRole("button", { name: "Enviar otro código en 60 s" }),
    ).toBeDisabled();
    expect(screen.queryByText(/Demasiados intentos/)).toBeNull();
  });

  it.each([
    [reply(400, { code: "resend_unavailable", message: "x" }), /Ahora no se puede enviar otro/],
    [() => Promise.reject(new TypeError("Failed to fetch")), /No se pudo conectar/],
    [reply(500, {}), /Algo falló en nuestro servidor/],
  ])("a refusal or a failure gives its message", async (answer, text) => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(reply(200, { ...STATUS, resend_in: 0 }), answer);
    renderPage(fetcher);

    await user.click(await screen.findByRole("button", { name: "Enviar otro código" }));

    expect(await screen.findByText(text)).toBeInTheDocument();
  });
});

describe("password step and account created", () => {
  async function acceptCode(
    user: ReturnType<typeof userEvent.setup>,
    ...after: (() => Promise<Response>)[]
  ) {
    openAt("/register/continue#pid-1");
    const answers = replies(reply(200, STATUS), reply(200, { result: "verified" }), ...after);
    const view = renderPage(answers.fetcher);
    await typeCode(user, "123456");
    await screen.findByRole("heading", { level: 2, name: "Elige tu contraseña" });
    return { ...answers, ...view };
  }

  async function sendPassword(user: ReturnType<typeof userEvent.setup>) {
    await user.type(screen.getByLabelText(/^Contraseña/), "turbina-compresor-7");
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));
  }

  it("an accepted code shows the password step and keeps the code only in memory", async () => {
    const user = userEvent.setup();
    await acceptCode(user);

    expect(screen.queryByRole("textbox", { name: "Código de verificación" })).toBeNull();
    expect(window.location.href).not.toContain("123456");
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain("123456");
  });

  it("with the account created, goes to the account created screen", async () => {
    const user = userEvent.setup();
    const { calls } = await acceptCode(user, reply(201, { result: "created" }));

    await sendPassword(user);

    await waitFor(() => expect(window.location.pathname).toBe("/register/done"));
    expect(calls[2].body).toEqual({
      public_id: "pid-1",
      code: "123456",
      password: "turbina-compresor-7",
      language: "es",
    });
  });

  it("a refused code goes back to the verification with its message and without the code", async () => {
    const user = userEvent.setup();
    const { calls } = await acceptCode(
      user,
      reply(400, { code: "wrong_code", message: "x" }),
      reply(200, STATUS),
    );

    await sendPassword(user);

    const field = await screen.findByRole("textbox", { name: "Código de verificación" });
    expect(field).toHaveValue("");
    expect(screen.getByText(/El código no es correcto/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 2, name: "Elige tu contraseña" })).toBeNull();
    expect(calls.map((call) => call.url.split("/").pop())).toEqual([
      "status",
      "verify",
      "complete",
      "status",
    ]);
  });

  it("an identifier that disappears at the end shows the invalid link", async () => {
    const user = userEvent.setup();
    await acceptCode(user, reply(404, { code: "not_found", message: "x" }));

    await sendPassword(user);

    expect(
      await screen.findByRole("heading", { level: 1, name: "Enlace no válido" }),
    ).toBeVisible();
  });

  it("reloading goes back to the verification", async () => {
    const user = userEvent.setup();
    const { fetcher, unmount } = await acceptCode(user, reply(200, STATUS));
    unmount();

    renderPage(fetcher);

    expect(await screen.findByRole("textbox", { name: "Código de verificación" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2, name: "Elige tu contraseña" })).toBeNull();
  });
});

test("the account created screen says so without signing in", () => {
  render(
    <I18nextProvider i18n={createI18n("es")}>
      <DonePage />
    </I18nextProvider>,
  );

  expect(screen.getByRole("heading", { level: 1, name: "Cuenta creada" })).toBeVisible();
  expect(screen.getByText("Tu cuenta se ha creado.")).toBeVisible();
  expect(screen.queryByRole("textbox")).toBeNull();
  expect(screen.queryByLabelText(/Contraseña/)).toBeNull();
});

describe("the two buttons in one row", () => {
  it("both go in the same row of the form, with the secondary one before the main one", async () => {
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(reply(200, { ...STATUS, resend_in: 0 }));
    const { container } = renderPage(fetcher);

    const resend = await screen.findByRole("button", { name: "Enviar otro código" });
    const verify = screen.getByRole("button", { name: "Verificar" });

    const row = container.querySelector("form .form-actions") as HTMLElement;
    expect(row).toContainElement(resend);
    expect(row).toContainElement(verify);
    expect([...row.children]).toEqual([resend, verify]);
    expect(resend).toHaveAttribute("data-ui", "button-secondary");
    expect(verify).toHaveAttribute("data-ui", "button-primary");
    expect(row.parentElement?.tagName).toBe("FORM");
  });

  it("the resend button is not a submit button: it does not send the code", async () => {
    const user = userEvent.setup();
    openAt("/register/continue#pid-1");
    const { calls, fetcher } = replies(
      reply(200, { ...STATUS, resend_in: 0 }),
      reply(202, { result: "resent" }),
      reply(200, STATUS),
    );
    renderPage(fetcher);
    await user.type(
      await screen.findByRole("textbox", { name: /Código de verificación/ }),
      "123456",
    );

    const resend = screen.getByRole("button", { name: "Enviar otro código" });
    expect(resend).toHaveAttribute("type", "button");
    await user.click(resend);

    await screen.findByText("Códigos que aún puedes pedir: 5.");
    expect(calls.map((call) => call.url.split("/").pop())).toEqual(["status", "resend", "status"]);
  });

  it("the main button still sends the code and is the only submit of the form", async () => {
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(reply(200, STATUS));
    const { container } = renderPage(fetcher);

    const verify = await screen.findByRole("button", { name: "Verificar" });

    expect(verify).toHaveAttribute("type", "submit");
    expect(container.querySelectorAll("form button[type='submit']")).toHaveLength(1);
  });

  it("the resend button keeps its countdown and its lock inside the row", async () => {
    openAt("/register/continue#pid-1");
    const { fetcher } = replies(reply(200, { ...STATUS, resend_in: 30, resends_left: 0 }));
    const { container } = renderPage(fetcher);

    const resend = await screen.findByRole("button", { name: "Enviar otro código en 30 s" });

    expect(resend).toBeDisabled();
    expect(container.querySelector(".form-actions")).toContainElement(resend);
  });
});
