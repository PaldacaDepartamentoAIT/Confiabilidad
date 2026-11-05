import { createClient, detectClientKind, environmentConfig, type ClientConfig } from "./client";

type Call = { url: string; init: RequestInit };

function fakeFetch(response: Response | Error) {
  const calls: Call[] = [];
  const fetcher = (url: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return response instanceof Error ? Promise.reject(response) : Promise.resolve(response);
  };
  return { calls, fetcher: fetcher as typeof fetch };
}

function json(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

function config(fetcher: typeof fetch, overrides: Partial<ClientConfig> = {}): ClientConfig {
  return { kind: "browser", appBaseUrl: "", language: () => "pt-BR", fetch: fetcher, ...overrides };
}

afterEach(() => {
  vi.unstubAllEnvs();
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
});

describe("cliente de la API", () => {
  it("usa las rutas del navegador con el token CSRF de la cookie", async () => {
    document.cookie = "csrftoken=token-123";
    const { calls, fetcher } = fakeFetch(json(200, { result: "verified" }));

    const result = await createClient(config(fetcher)).post("registration/verify", { code: "1" });

    expect(result).toEqual({ kind: "ok", status: 200, data: { result: "verified" } });
    expect(calls[0].url).toBe("/api/browser/v1/registration/verify");
    const headers = new Headers(calls[0].init.headers);
    expect(headers.get("X-CSRFToken")).toBe("token-123");
    expect(headers.get("Accept-Language")).toBe("pt-BR");
    expect(calls[0].init.credentials).toBe("same-origin");
    expect(JSON.parse(String(calls[0].init.body))).toEqual({ code: "1", language: "pt-BR" });
  });

  it("usa las rutas de la aplicación en Tauri, sin CSRF ni cookies", async () => {
    document.cookie = "csrftoken=token-123";
    const { calls, fetcher } = fakeFetch(json(202, { result: "resent" }));
    const client = createClient(
      config(fetcher, { kind: "app", appBaseUrl: "https://api.example" }),
    );

    await client.post("registration/resend", { public_id: "p" });

    expect(calls[0].url).toBe("https://api.example/api/app/v1/registration/resend");
    expect(new Headers(calls[0].init.headers).has("X-CSRFToken")).toBe(false);
    expect(calls[0].init.credentials).toBe("omit");
  });

  it("pide los GET con el idioma en la consulta", async () => {
    const { calls, fetcher } = fakeFetch(json(200, { countries: [] }));

    await createClient(config(fetcher)).get("registration/options");

    expect(calls[0].url).toBe("/api/browser/v1/registration/options?language=pt-BR");
    expect(calls[0].init.method).toBe("GET");
  });

  it("devuelve los códigos de los errores de cada campo", async () => {
    const body = { errors: { name: [{ code: "name_empty", message: "x" }], email: [] } };
    const { fetcher } = fakeFetch(json(400, body));

    const result = await createClient(config(fetcher)).post("registration", {});

    expect(result).toEqual({ kind: "fieldErrors", errors: { name: ["name_empty"], email: [] } });
  });

  it("devuelve el código de un rechazo", async () => {
    const { fetcher } = fakeFetch(json(400, { code: "wrong_code", message: "x" }));

    const result = await createClient(config(fetcher)).post("registration/verify", {});

    expect(result).toEqual({ kind: "refused", code: "wrong_code" });
  });

  it("distingue el identificador no encontrado", async () => {
    const { fetcher } = fakeFetch(json(404, { code: "not_found", message: "x" }));

    expect(await createClient(config(fetcher)).post("registration/status", {})).toEqual({
      kind: "notFound",
    });
  });

  it("devuelve los segundos de espera del límite superado", async () => {
    const { fetcher } = fakeFetch(
      json(429, { message: "x", retry_after: 37 }, { "Retry-After": "37" }),
    );

    expect(await createClient(config(fetcher)).post("registration/verify", {})).toEqual({
      kind: "rateLimited",
      retryAfter: 37,
    });
  });

  it("toma la espera de la cabecera si el cuerpo no la trae", async () => {
    const { fetcher } = fakeFetch(json(429, {}, { "Retry-After": "12" }));

    expect(await createClient(config(fetcher)).post("registration/verify", {})).toEqual({
      kind: "rateLimited",
      retryAfter: 12,
    });
  });

  it.each([403, 500])("trata un %i como un fallo sin código", async (status) => {
    const { fetcher } = fakeFetch(new Response("<html>", { status }));

    expect(await createClient(config(fetcher)).post("registration", {})).toEqual({
      kind: "failed",
      status,
    });
  });

  it("distingue el fallo de red", async () => {
    const { fetcher } = fakeFetch(new TypeError("Failed to fetch"));

    expect(await createClient(config(fetcher)).post("registration", {})).toEqual({
      kind: "networkError",
    });
  });

  it("toma del entorno la URL de la aplicación y el tipo de cliente", () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example");

    const result = environmentConfig(() => "en");

    expect(result.kind).toBe("browser");
    expect(result.appBaseUrl).toBe("https://api.example");
    expect(result.language()).toBe("en");
  });

  it("deja vacía la URL de la aplicación si el entorno no la define", () => {
    vi.stubEnv("VITE_API_BASE_URL", undefined);

    expect(environmentConfig(() => "en").appBaseUrl).toBe("");
  });

  it("acepta una respuesta correcta sin cuerpo", async () => {
    const { fetcher } = fakeFetch(new Response(null, { status: 204 }));

    expect(await createClient(config(fetcher)).post("registration", {})).toEqual({
      kind: "ok",
      status: 204,
      data: null,
    });
  });

  it("omite el token CSRF si no hay cookie", async () => {
    const { calls, fetcher } = fakeFetch(json(200, {}));

    await createClient(config(fetcher)).post("registration", {});

    expect(new Headers(calls[0].init.headers).has("X-CSRFToken")).toBe(false);
  });

  it("detecta Tauri por su objeto global", () => {
    expect(detectClientKind({})).toBe("browser");
    expect(detectClientKind({ __TAURI_INTERNALS__: {} })).toBe("app");
  });
});
