import type { SelectOption } from "../components/fields/SelectField";

export function countryOptions(codes: readonly string[], language: string): SelectOption[] {
  const names = new Intl.DisplayNames([language], { type: "region" });
  return codes
    .map((code) => ({ value: code, label: names.of(code) ?? code }))
    .sort((first, second) => first.label.localeCompare(second.label, language));
}
