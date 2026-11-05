import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { createClient } from "../api/client";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { createI18n } from "../i18n";
import { PasswordStep } from "./PasswordStep";

function replies(...responses: (() => Promise<Response>)[]) {
  const bodies: unknown[] = [];
  const fetcher = (url: RequestInfo | URL, init?: RequestInit) => {
    bodies.push({ url: String(url), body: JSON.parse(String(init?.body)) as unknown });
    const next = responses.shift();
    return next ? next() : Promise.reject(new Error("unexpected call"));
  };
  return { bodies, fetcher: fetcher as typeof fetch };
}

const reply = (status: number, body: unknown) => () =>
  Promise.resolve(new Response(JSON.stringify(body), { status }));

function renderStep(fetcher: typeof fetch) {
  const i18n = createI18n("es");
  const client = createClient({
    kind: "browser",
    appBaseUrl: "",
    language: () => i18n.language,
    fetch: fetcher,
  });
  const onCreated = vi.fn();
  const onCodeRejected = vi.fn();
  render(
    <I18nextProvider i18n={i18n}>
      <LiveAnnouncer>
        <PasswordStep
          client={client}
          publicId="pid-1"
          code="123456"
          onCreated={onCreated}
          onCodeRejected={onCodeRejected}
        />
      </LiveAnnouncer>
    </I18nextProvider>,
  );
  return { onCreated, onCodeRejected };
}

const field = () => screen.getByLabelText(/^Contraseña/);

async function submit(user: ReturnType<typeof userEvent.setup>, password: string) {
  await user.type(field(), password);
  await user.click(screen.getByRole("button", { name: "Crear cuenta" }));
}

afterEach(() => {
  vi.useRealTimers();
});

test.each([
  ["corta", "Usa al menos 12 caracteres."],
  ["123456789012", "No uses solo números."],
])("the browser rejects %j without asking the server", async (password, message) => {
  const user = userEvent.setup();
  const { bodies, fetcher } = replies();
  renderStep(fetcher);

  await submit(user, password);

  expect(field()).toHaveAccessibleDescription(expect.stringContaining(message) as string);
  expect(bodies).toEqual([]);
});

test("sends the code and the password and warns when the account is created", async () => {
  const user = userEvent.setup();
  const { bodies, fetcher } = replies(reply(201, { result: "created" }));
  const { onCreated } = renderStep(fetcher);

  expect(screen.getByRole("heading", { level: 2, name: "Elige tu contraseña" })).toBeVisible();
  expect(field()).toHaveAttribute("autocomplete", "new-password");
  await submit(user, "turbina-compresor-7");

  await vi.waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));
  expect(bodies).toEqual([
    {
      url: "/api/browser/v1/registration/complete",
      body: { public_id: "pid-1", code: "123456", password: "turbina-compresor-7", language: "es" },
    },
  ]);
});

test("shows under the field every rule the server rejects", async () => {
  const user = userEvent.setup();
  const errors = {
    password: [
      { code: "password_too_common", message: "x" },
      { code: "password_pwned", message: "x" },
    ],
  };
  const { fetcher } = replies(reply(400, { errors }));
  const { onCodeRejected } = renderStep(fetcher);

  await submit(user, "turbina-compresor-7");

  await vi.waitFor(() =>
    expect(field()).toHaveAccessibleDescription(
      expect.stringContaining(
        "Esta contraseña es demasiado común. Esta contraseña ha aparecido en filtraciones de datos. Elige otra.",
      ) as string,
    ),
  );
  expect(field()).toHaveFocus();
  expect(onCodeRejected).not.toHaveBeenCalled();
});

test.each([
  [reply(400, { code: "wrong_code", message: "x" }), "wrong_code"],
  [reply(400, { code: "locked", message: "x" }), "locked"],
  [reply(404, { code: "not_found", message: "x" }), "not_found"],
])("a refused code is passed on to whoever holds it", async (answer, code) => {
  const user = userEvent.setup();
  const { fetcher } = replies(answer);
  const { onCodeRejected, onCreated } = renderStep(fetcher);

  await submit(user, "turbina-compresor-7");

  await vi.waitFor(() => expect(onCodeRejected).toHaveBeenCalledWith(code));
  expect(onCreated).not.toHaveBeenCalled();
});

test("over the limit, counts down and allows sending again at zero", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  const { fetcher } = replies(reply(429, { message: "x", retry_after: 2 }));
  renderStep(fetcher);

  await submit(user, "turbina-compresor-7");

  expect(
    await screen.findByText("Demasiados intentos. Vuelve a intentarlo en 2 s."),
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Crear cuenta" })).toBeDisabled();
  await act(() => vi.advanceTimersByTimeAsync(2000));
  expect(screen.getByRole("button", { name: "Crear cuenta" })).toBeEnabled();
  expect(field()).toHaveValue("turbina-compresor-7");
});

test.each([
  [() => Promise.reject(new TypeError("Failed to fetch")), /No se pudo conectar/],
  [reply(500, {}), /Algo falló en nuestro servidor/],
])("a failure gives a general message and keeps the password", async (answer, text) => {
  const user = userEvent.setup();
  const { fetcher } = replies(answer);
  renderStep(fetcher);

  await submit(user, "turbina-compresor-7");

  expect(await screen.findByText(text)).toHaveFocus();
  expect(field()).toHaveValue("turbina-compresor-7");
});

test("while waiting for the answer, a second submission sends nothing", async () => {
  const user = userEvent.setup();
  const { bodies, fetcher } = replies(() => new Promise<Response>(() => {}));
  renderStep(fetcher);

  await user.type(field(), "turbina-compresor-7");
  const form = field().closest("form") as HTMLFormElement;
  fireEvent.submit(form);
  fireEvent.submit(form);

  await vi.waitFor(() => expect(bodies).toHaveLength(1));
  expect(bodies).toHaveLength(1);
});

test("leaving the password field checks it without asking the server", async () => {
  const user = userEvent.setup();
  const { bodies, fetcher } = replies();
  renderStep(fetcher);

  await user.type(field(), "corta");
  // El campo y su botón de mostrar cuentan como uno: se sale al dejar los dos (RF-025 de la base).
  await user.tab();
  await user.tab();

  expect(field()).toHaveAccessibleDescription(
    expect.stringContaining("Usa al menos 12 caracteres.") as string,
  );
  expect(bodies).toEqual([]);
});
