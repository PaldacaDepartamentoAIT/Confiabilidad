export const CODE_LENGTH = 6;

// Primer carácter de cada serie de dígitos aceptada: ASCII, ancho completo y arábigos (RF-013).
const DIGIT_ZEROS = [0x30, 0xff10, 0x0660];

function toAsciiDigit(character: string): string | null {
  const codePoint = character.codePointAt(0) ?? 0;
  for (const zero of DIGIT_ZEROS) {
    const value = codePoint - zero;
    if (value >= 0 && value <= 9) return String(value);
  }
  return null;
}

function digitsOf(text: string): string {
  return Array.from(text, toAsciiDigit).join("");
}

export function normalizeTypedCode(value: string): string {
  return digitsOf(value).slice(0, CODE_LENGTH);
}

export function extractPastedCode(text: string): string | null {
  const digits = digitsOf(text);
  return digits ? digits.slice(0, CODE_LENGTH) : null;
}
