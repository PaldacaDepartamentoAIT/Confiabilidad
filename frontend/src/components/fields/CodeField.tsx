import { forwardRef, useState, type ClipboardEvent, type ComponentProps } from "react";

import { extractPastedCode, normalizeTypedCode } from "./code";
import { TextField } from "./TextField";

type CodeFieldProps = Omit<
  ComponentProps<typeof TextField>,
  "type" | "adornment" | "value" | "defaultValue" | "onChange" | "onPaste"
> & {
  defaultValue?: string;
  onValueChange?: (code: string) => void;
};

export const CodeField = forwardRef<HTMLInputElement, CodeFieldProps>(function CodeField(
  { defaultValue = "", onValueChange, ...fieldProps },
  ref,
) {
  const [code, setCode] = useState(() => normalizeTypedCode(defaultValue));

  function update(next: string) {
    setCode(next);
    onValueChange?.(next);
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
    event.preventDefault();
    const pasted = extractPastedCode(event.clipboardData.getData("text"));
    if (pasted !== null) update(pasted);
  }

  return (
    <TextField
      {...fieldProps}
      ref={ref}
      type="text"
      inputMode="numeric"
      autoComplete="one-time-code"
      value={code}
      onChange={(event) => update(normalizeTypedCode(event.target.value))}
      onPaste={handlePaste}
    />
  );
});
