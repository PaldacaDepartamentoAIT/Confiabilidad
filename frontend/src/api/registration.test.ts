import type { ApiClient, ApiResult } from "./client";
import {
  completeRegistration,
  fetchOptions,
  fetchStatus,
  resendCode,
  submitRegistration,
  verifyCode,
} from "./registration";

type Sent = { method: "get" | "post"; path: string; body?: Record<string, unknown> };

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
  };
  return { client, sent };
}

const form = {
  name: "Ana",
  birthdate: "1990-04-02",
  email: "ana@example.com",
  country: "BR",
  terms: { version: "1", locale: "es" },
};

describe("llamadas del registro", () => {
  it("pide las opciones del formulario", async () => {
    const options = { countries: ["BR"], terms: null, marketing: null };
    const { client, sent } = recordingClient({ kind: "ok", status: 200, data: options });

    expect(await fetchOptions(client)).toEqual({ kind: "ok", status: 200, data: options });
    expect(sent).toEqual([{ method: "get", path: "registration/options" }]);
  });

  it("envía el formulario con los términos aceptados y sin marketing si no se pasa", async () => {
    const { client, sent } = recordingClient();

    await submitRegistration(client, form);

    expect(sent).toEqual([
      {
        method: "post",
        path: "registration",
        body: {
          name: "Ana",
          birthdate: "1990-04-02",
          email: "ana@example.com",
          country: "BR",
          terms: { accepted: true, version: "1", locale: "es" },
        },
      },
    ]);
    expect(sent[0].body).not.toHaveProperty("marketing");
  });

  it("incluye el marketing cuando se pasa", async () => {
    const { client, sent } = recordingClient();

    await submitRegistration(client, { ...form, marketing: { version: "2", locale: "es" } });

    expect(sent[0].body?.marketing).toEqual({ version: "2", locale: "es" });
  });

  it("consulta el estado con el identificador en el cuerpo", async () => {
    const { client, sent } = recordingClient();

    await fetchStatus(client, "abc");

    expect(sent).toEqual([
      { method: "post", path: "registration/status", body: { public_id: "abc" } },
    ]);
  });

  it("verifica el código", async () => {
    const { client, sent } = recordingClient();

    await verifyCode(client, "abc", "123456");

    expect(sent).toEqual([
      { method: "post", path: "registration/verify", body: { public_id: "abc", code: "123456" } },
    ]);
  });

  it("pide el reenvío", async () => {
    const { client, sent } = recordingClient();

    await resendCode(client, "abc");

    expect(sent).toEqual([
      { method: "post", path: "registration/resend", body: { public_id: "abc" } },
    ]);
  });

  it("completa con el código y la contraseña", async () => {
    const { client, sent } = recordingClient({ kind: "refused", code: "locked" });

    expect(await completeRegistration(client, "abc", "123456", "contraseña larga")).toEqual({
      kind: "refused",
      code: "locked",
    });
    expect(sent).toEqual([
      {
        method: "post",
        path: "registration/complete",
        body: { public_id: "abc", code: "123456", password: "contraseña larga" },
      },
    ]);
  });
});
