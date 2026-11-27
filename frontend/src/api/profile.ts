import type { ApiClient, ApiResult } from "./client";

export type DisableBlockReason = "owns_company" | "last_superuser";

export type ProfileData = {
  email: string;
  name: string;
  birthdate: string;
  country: string;
  can_disable?: boolean;
  disable_block_reason?: DisableBlockReason | null;
  disable_retry_after?: number;
};

export type ProfileUpdate = {
  name?: string;
  birthdate?: string;
  country?: string;
};

export type PasswordChange = {
  current_password: string;
  new_password: string;
};

export type AccountDisablePayload = {
  current_password: string;
};

const DISABLED_NOTICE_KEY = "confiabilidad.accountDisabled";

export function markAccountDisabledNotice(): void {
  try {
    window.sessionStorage.setItem(DISABLED_NOTICE_KEY, "1");
  } catch {
    // Algunos contextos embebidos restringen sessionStorage; la redirección sigue funcionando.
  }
}

export function consumeAccountDisabledNotice(): boolean {
  try {
    if (window.sessionStorage.getItem(DISABLED_NOTICE_KEY) !== "1") return false;
    window.sessionStorage.removeItem(DISABLED_NOTICE_KEY);
    return true;
  } catch {
    return false;
  }
}

export function getProfile(client: ApiClient): Promise<ApiResult<ProfileData>> {
  return client.get("auth/profile");
}

export function updateProfile(
  client: ApiClient,
  data: ProfileUpdate,
): Promise<ApiResult<ProfileData>> {
  return client.patch("auth/profile", data);
}

export function changePassword(
  client: ApiClient,
  data: PasswordChange,
): Promise<ApiResult<{ result: string }>> {
  return client.post("auth/password/change", data);
}

export function disableAccount(
  client: ApiClient,
  data: AccountDisablePayload,
): Promise<ApiResult<{ result: string }>> {
  return client.post("auth/account/disable", data);
}
