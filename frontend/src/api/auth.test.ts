import { createTokenStorage } from "../auth/tokenStorage";
import {
  acceptTerms,
  getSession,
  listSessions,
  login,
  logout,
  revokeOtherSessions,
  revokeSession,
} from "./auth";
import type { ApiClient, ApiResult } from "./client";

type Sent = { method: "get" | "post" | "patch"; path: string; body?: Record<string, unknown> };

function recordingClient(result: ApiResult = { kind: "ok", status: 200, data: {} }) {
  const sent: Sent[] = [];
  const client: ApiClient = {
    get: <Data>(path: string) => {
      sent.push({ method: "get", path });
      return Promise.resolve(result as ApiResult<Data>);
    },
    post: <Data>(path: string, body: Record<string, unknown>) => {
      sent.push({ method: "post", path, body });
      return Promise.resolve(result as ApiResult<Data>);
    },
    patch: <Data>(path: string, body: Record<string, unknown>) => {
      sent.push({ method: "patch", path, body });
      return Promise.resolve(result as ApiResult<Data>);
    },
  };
  return { client, sent };
}

describe("llamadas de autenticación y sesiones", () => {
  it("consulta la sesión activa", async () => {
    const info = {
      user: { email: "ana@example.com", name: "Ana" },
      terms_status: "accepted" as const,
      terms: null,
    };
    const { client, sent } = recordingClient({ kind: "ok", status: 200, data: info });

    expect(await getSession(client)).toEqual({ kind: "ok", status: 200, data: info });
    expect(sent).toEqual([{ method: "get", path: "auth/session" }]);
  });

  it("inicia sesión y guarda el token solo cuando viene en la respuesta (app)", async () => {
    const storage = createTokenStorage(null);
    const { client: appClient, sent } = recordingClient({
      kind: "ok",
      status: 200,
      data: {
        user: { email: "ana@example.com", name: "Ana" },
        terms_status: "accepted",
        terms: null,
        session_token: "tok-123",
      },
    });

    await login(appClient, { email: "ana@example.com", password: "secret" }, storage);

    expect(sent).toEqual([
      {
        method: "post",
        path: "auth/login",
        body: { email: "ana@example.com", password: "secret" },
      },
    ]);
    expect(storage.get()).toBe("tok-123");

    const webStorage = createTokenStorage(null);
    const { client: webClient } = recordingClient({
      kind: "ok",
      status: 200,
      data: {
        user: { email: "ana@example.com", name: "Ana" },
        terms_status: "accepted",
        terms: null,
      },
    });
    await login(webClient, { email: "ana@example.com", password: "secret" }, webStorage);
    expect(webStorage.get()).toBeNull();
  });

  it.each<ApiResult>([
    { kind: "ok", status: 200, data: { result: "logged_out" } },
    { kind: "unauthenticated" },
    { kind: "networkError" },
  ])("cierra sesión y borra siempre el token local (%o)", async (outcome) => {
    const storage = createTokenStorage(null);
    storage.set("tok-active");
    const { client, sent } = recordingClient(outcome);

    const res = await logout(client, storage);

    expect(res).toEqual(outcome);
    expect(sent).toEqual([{ method: "post", path: "auth/logout", body: {} }]);
    expect(storage.get()).toBeNull();
  });

  it("envía la aceptación de términos y las operaciones de sesiones", async () => {
    const { client, sent } = recordingClient();

    await acceptTerms(client, { version: "1", locale: "es" });
    await listSessions(client);
    await revokeSession(client, 42);
    await revokeOtherSessions(client);

    expect(sent).toEqual([
      {
        method: "post",
        path: "auth/terms/accept",
        body: { version: "1", locale: "es", accepted: true },
      },
      { method: "get", path: "auth/sessions" },
      { method: "post", path: "auth/sessions/revoke", body: { session_id: 42 } },
      { method: "post", path: "auth/sessions/revoke-others", body: {} },
    ]);
  });
});
