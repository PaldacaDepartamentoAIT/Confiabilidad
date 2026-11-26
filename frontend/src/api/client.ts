import { tokenStorage, type TokenStorage } from "../auth/tokenStorage";

export type ClientKind = "browser" | "app";

export type TermsStatus = "accepted" | "not_accepted" | "no_current_version";

export type ClientConfig = {
  kind: ClientKind;
  appBaseUrl: string;
  language: () => string;
  fetch: typeof fetch;
  tokenStorage?: TokenStorage;
};

export type ApiResult<Data = unknown> =
  | { kind: "ok"; status: number; data: Data }
  | { kind: "fieldErrors"; errors: Record<string, string[]> }
  | { kind: "refused"; code: string }
  | { kind: "unauthenticated" }
  | { kind: "termsRequired"; termsStatus: TermsStatus }
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

function isTermsStatus(value: unknown): value is TermsStatus {
  return value === "accepted" || value === "not_accepted" || value === "no_current_version";
}

async function interpret<Data>(response: Response): Promise<ApiResult<Data>> {
  const text = await response.text();
  const body = text === "" ? null : parseJson(text);
  if (response.ok && body !== undefined) {
    return { kind: "ok", status: response.status, data: body as Data };
  }
  if (response.status === 401) return { kind: "unauthenticated" };
  if (response.status === 403 && isRecord(body) && body.code === "terms_required") {
    return {
      kind: "termsRequired",
      termsStatus: isTermsStatus(body.terms_status) ? body.terms_status : "not_accepted",
    };
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
  const inflight = new Map<string, Promise<ApiResult<unknown>>>();

  async function send<Data>(path: string, init: RequestInit): Promise<ApiResult<Data>> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    headers.set("Accept-Language", config.language());
    let credentials: RequestCredentials = "omit";
    if (config.kind === "browser") {
      credentials = "same-origin";
      const token = readCookie(CSRF_COOKIE);
      if (token !== null) headers.set("X-CSRFToken", token);
    } else {
      const token = (config.tokenStorage ?? tokenStorage).get();
      if (token !== null && token !== "") headers.set("X-Session-Token", token);
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
    get: <Data>(path: string) => {
      const target = `${path}?language=${encodeURIComponent(config.language())}`;
      const token =
        config.kind === "app" ? ((config.tokenStorage ?? tokenStorage).get() ?? "") : "";
      const key = `${target}\0${token}`;
      const pending = inflight.get(key) as Promise<ApiResult<Data>> | undefined;
      if (pending) return pending;
      const request = send<Data>(target, { method: "GET" }).finally(() => inflight.delete(key));
      inflight.set(key, request);
      return request;
    },
    post: (path, body) =>
      send(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...body, language: config.language() }),
      }),
  };
}
