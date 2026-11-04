import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";

import { createClient } from "../api/client";
import type { RegistrationStatus } from "../api/registration";
import { LiveAnnouncer } from "../components/LiveAnnouncer";
import { createI18n } from "../i18n";
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
  act(() => {
    vi.advanceTimersByTime(2000);
  });
  expect(screen.getByText("El código caduca en 0:59.")).toBeInTheDocument();

  act(() => {
    vi.advanceTimersByTime(59_000);
  });
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
