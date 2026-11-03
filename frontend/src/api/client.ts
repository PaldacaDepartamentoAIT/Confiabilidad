export type ClientKind = "browser" | "app";

export type ClientConfig = {
  kind: ClientKind;
  appBaseUrl: string;
  language: () => string;
  fetch: typeof fetch;
};

export type ApiResult<Data = unknown> =
  | { kind: "ok"; status: number; data: Data }
  | { kind: "fieldErrors"; errors: Record<string, string[]> }
  | { kind: "refused"; code: string }
  | { kind: "notFound" }
  | { kind: "rateLimited"; retryAfter: number }
  | { kind: "failed"; status: number }
  | { kind: "networkError" };

export type ApiClient = {
  get: <Data = unknown>(path: string) => Promise<ApiResult<Data>>;
  post: <Data = unknown>(path: string, body: Record<string, unknown>) => Promise<ApiResult<Data>>;
};

const CSRF_COOKIE = "csrftoken";

export function detectClientKind(win: object): ClientKind {
  return "__TAURI_INTERNALS__" in win ? "app" : "browser";
}

export function environmentConfig(language: () => string): ClientConfig {
  return {
    kind: detectClientKind(window),
    appBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "",
    language,
    fetch: (input, init) => window.fetch(input, init),
  };
}

function readCookie(name: string): string | null {
  const entry = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name}=`));
  return entry === undefined ? null : decodeURIComponent(entry.slice(name.length + 1));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function errorCodes(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) =>
    isRecord(item) && typeof item.code === "string" ? [item.code] : [],
  );
}

function parseJson(text: string): unknown {
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return undefined;
  }
}

function retryAfter(body: unknown, response: Response): number {
  if (isRecord(body) && typeof body.retry_after === "number") return body.retry_after;
  return Number(response.headers.get("Retry-After") ?? 0);
}

async function interpret<Data>(response: Response): Promise<ApiResult<Data>> {
  const text = await response.text();
  const body = text === "" ? null : parseJson(text);
  if (response.ok && body !== undefined) {
    return { kind: "ok", status: response.status, data: body as Data };
  }
  if (response.status === 404) return { kind: "notFound" };
  if (response.status === 429)
    return { kind: "rateLimited", retryAfter: retryAfter(body, response) };
  if (response.status === 400 && isRecord(body)) {
    if (isRecord(body.errors)) {
      const errors = Object.fromEntries(
        Object.entries(body.errors).map(([field, list]) => [field, errorCodes(list)]),
      );
      return { kind: "fieldErrors", errors };
    }
    if (typeof body.code === "string") return { kind: "refused", code: body.code };
  }
  return { kind: "failed", status: response.status };
}

export function createClient(config: ClientConfig): ApiClient {
  const base = config.kind === "app" ? `${config.appBaseUrl}/api/app/v1` : "/api/browser/v1";

  async function send<Data>(path: string, init: RequestInit): Promise<ApiResult<Data>> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    headers.set("Accept-Language", config.language());
    let credentials: RequestCredentials = "omit";
    if (config.kind === "browser") {
      credentials = "same-origin";
      const token = readCookie(CSRF_COOKIE);
      if (token !== null) headers.set("X-CSRFToken", token);
    }
    let response: Response;
    try {
      response = await config.fetch(`${base}/${path}`, { ...init, headers, credentials });
    } catch {
      return { kind: "networkError" };
    }
    return interpret<Data>(response);
  }

  return {
    get: (path) =>
      send(`${path}?language=${encodeURIComponent(config.language())}`, { method: "GET" }),
    post: (path, body) =>
      send(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...body, language: config.language() }),
      }),
  };
}
