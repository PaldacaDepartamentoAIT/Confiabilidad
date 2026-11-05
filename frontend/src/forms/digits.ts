// Caracteres que `str.isdigit()` de Python acepta además de la categoría `Nd`: los de
// `Numeric_Type=Digit` (superíndices, subíndices, dígitos rodeados…), que `\p{Nd}` no cubre (D-12).
// Generado con Python 3.12 (Unicode 15.0, el del backend) y agrupado en rangos:
//   python3 -c "import sys, unicodedata; print([c for c in map(chr, range(sys.maxunicode + 1))
//   if c.isdigit() and unicodedata.category(c) != 'Nd'])"
const NON_DECIMAL_DIGITS =
  "\\u{B2}-\\u{B3}\\u{B9}\\u{1369}-\\u{1371}\\u{19DA}\\u{2070}\\u{2074}-\\u{2079}\\u{2080}-\\u{2089}" +
  "\\u{2460}-\\u{2468}\\u{2474}-\\u{247C}\\u{2488}-\\u{2490}\\u{24EA}\\u{24F5}-\\u{24FD}\\u{24FF}" +
  "\\u{2776}-\\u{277E}\\u{2780}-\\u{2788}\\u{278A}-\\u{2792}\\u{10A40}-\\u{10A43}" +
  "\\u{10E60}-\\u{10E68}\\u{11052}-\\u{1105A}\\u{1F100}-\\u{1F10A}";

export const ONLY_DIGITS = new RegExp(`^[\\p{Nd}${NON_DECIMAL_DIGITS}]+$`, "u");
