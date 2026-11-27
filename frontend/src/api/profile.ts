import type { ApiClient, ApiResult } from "./client";

export type ProfileData = {
  email: string;
  name: string;
  birthdate: string;
  country: string;
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
