import { tokenStorage, type TokenStorage } from "../auth/tokenStorage";
import type { ApiClient, ApiResult, TermsStatus } from "./client";
import type { DocumentRef, LegalDocument } from "./registration";

export type AuthenticatedUser = {
  email: string;
  name: string;
};

export type SessionInfo = {
  user: AuthenticatedUser;
  terms_status: TermsStatus;
  terms: LegalDocument | null;
  session_token?: string;
};

export type ActiveSessionItem = {
  id: number;
  ip: string;
  user_agent: string;
  created_at: string;
  last_seen_at: string;
  is_current: boolean;
};

export type SessionsListResponse = {
  sessions: ActiveSessionItem[];
};

export type TermsAcceptOutcome = {
  terms_status: "accepted";
};

export type RevokeOutcome = {
  result: "revoked";
  revoked_count?: number;
};

export type LogoutOutcome = {
  result: "logged_out";
};

export function getSession(client: ApiClient): Promise<ApiResult<SessionInfo>> {
  return client.get("auth/session");
}

export async function login(
  client: ApiClient,
  credentials: { email: string; password: string },
  storage: TokenStorage = tokenStorage,
): Promise<ApiResult<SessionInfo>> {
  const result = await client.post<SessionInfo>("auth/login", credentials);
  if (
    result.kind === "ok" &&
    typeof result.data.session_token === "string" &&
    result.data.session_token !== ""
  ) {
    storage.set(result.data.session_token);
  }
  return result;
}

export async function logout(
  client: ApiClient,
  storage: TokenStorage = tokenStorage,
): Promise<ApiResult<LogoutOutcome>> {
  try {
    return await client.post<LogoutOutcome>("auth/logout", {});
  } finally {
    storage.clear();
  }
}

export function acceptTerms(
  client: ApiClient,
  terms: DocumentRef,
): Promise<ApiResult<TermsAcceptOutcome>> {
  return client.post("auth/terms/accept", { ...terms, accepted: true });
}

export function listSessions(client: ApiClient): Promise<ApiResult<SessionsListResponse>> {
  return client.get("auth/sessions");
}

export function revokeSession(
  client: ApiClient,
  sessionId: number,
): Promise<ApiResult<RevokeOutcome>> {
  return client.post("auth/sessions/revoke", { session_id: sessionId });
}

export function revokeOtherSessions(client: ApiClient): Promise<ApiResult<RevokeOutcome>> {
  return client.post("auth/sessions/revoke-others", {});
}
