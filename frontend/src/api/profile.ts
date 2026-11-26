import type { ApiClient, ApiResult } from "./client";

export type ProfileData = {
  email: string;
  name: string;
  birthdate: string;
  country: string;
};

export function getProfile(client: ApiClient): Promise<ApiResult<ProfileData>> {
  return client.get("auth/profile");
}
