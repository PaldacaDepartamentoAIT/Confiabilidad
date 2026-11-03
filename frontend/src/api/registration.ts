import type { ApiClient, ApiResult } from "./client";

export type DocumentRef = { version: string; locale: string };

export type LegalDocument = DocumentRef & { content: string };

export type RegistrationOptions = {
  countries: string[];
  terms: LegalDocument | null;
  marketing: LegalDocument | null;
};

export type RegistrationForm = {
  name: string;
  birthdate: string;
  email: string;
  country: string;
  terms: DocumentRef;
  marketing?: DocumentRef;
};

export type Started = { public_id: string; message: string };

export type RegistrationStatus = {
  code_expires_in: number;
  resend_in: number;
  resends_left: number;
  locked: boolean;
  expired: boolean;
};

export type FlowOutcome = { result: string };

export function fetchOptions(client: ApiClient): Promise<ApiResult<RegistrationOptions>> {
  return client.get("registration/options");
}

export function submitRegistration(
  client: ApiClient,
  form: RegistrationForm,
): Promise<ApiResult<Started>> {
  const { marketing, terms, ...fields } = form;
  return client.post("registration", {
    ...fields,
    terms: { accepted: true, ...terms },
    ...(marketing === undefined ? {} : { marketing }),
  });
}

export function fetchStatus(
  client: ApiClient,
  publicId: string,
): Promise<ApiResult<RegistrationStatus>> {
  return client.post("registration/status", { public_id: publicId });
}

export function verifyCode(
  client: ApiClient,
  publicId: string,
  code: string,
): Promise<ApiResult<FlowOutcome>> {
  return client.post("registration/verify", { public_id: publicId, code });
}

export function resendCode(client: ApiClient, publicId: string): Promise<ApiResult<FlowOutcome>> {
  return client.post("registration/resend", { public_id: publicId });
}

export function completeRegistration(
  client: ApiClient,
  publicId: string,
  code: string,
  password: string,
): Promise<ApiResult<FlowOutcome>> {
  return client.post("registration/complete", { public_id: publicId, code, password });
}
