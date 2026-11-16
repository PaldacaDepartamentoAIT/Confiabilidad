// Compara la estructura visual (estilos calculados) de los componentes marcados con
// data-ui entre una página de referencia y una candidata, en tema claro y oscuro.
// Uso: node comparar.cjs <referencia.html> <candidata.html>
const path = require('path');
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch {
  console.error('Falta Playwright. Instálalo fuera del repositorio o usa el que trae el entorno.');
  process.exit(2);
}

const PROPS = [
  'fontSize', 'fontWeight', 'fontFamily', 'lineHeight', 'letterSpacing', 'color',
  'backgroundColor', 'borderTopWidth', 'borderTopColor', 'borderBottomWidth',
  'borderBottomColor', 'borderLeftWidth', 'borderTopLeftRadius', 'paddingTop',
  'paddingRight', 'paddingBottom', 'paddingLeft',
];
// Alto de los componentes cuyo ancho depende del texto; ancho y alto de los de tamaño fijo.
const HEIGHT_ONLY = new Set([
  'nav-item', 'nav-item-active', 'sidebar-button', 'topbar', 'tab', 'tab-active', 'search',
  'button-primary', 'button-secondary',
]);
const FIXED = new Set(['sidebar-header', 'menu-toggle', 'avatar']);

async function measure(browser, file, scheme) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: scheme });
  const page = await ctx.newPage();
  await page.goto('file://' + path.resolve(file));
  await page.waitForTimeout(700);
  const data = await page.evaluate(({ PROPS, FIXED, HEIGHT_ONLY }) => {
    const out = {};
    document.querySelectorAll('[data-ui]').forEach((el) => {
      const key = el.getAttribute('data-ui');
      if (out[key]) return;
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      const v = {};
      PROPS.forEach((p) => (v[p] = s[p]));
      if (r.width === 0 || r.height === 0) return;
      if (FIXED.includes(key)) v.width = Math.round(r.width * 10) / 10;
      if (FIXED.includes(key) || HEIGHT_ONLY.includes(key)) v.height = Math.round(r.height * 10) / 10;
      out[key] = v;
    });
    return out;
  }, { PROPS, FIXED: [...FIXED], HEIGHT_ONLY: [...HEIGHT_ONLY] });
  await ctx.close();
  return data;
}

(async () => {
  const [ref, cand] = process.argv.slice(2);
  if (!ref || !cand) {
    console.error('Uso: node comparar.cjs <referencia.html> <candidata.html>');
    process.exit(2);
  }
  const browser = await chromium.launch();
  let diffs = 0;
  for (const scheme of ['light', 'dark']) {
    const a = await measure(browser, ref, scheme);
    const b = await measure(browser, cand, scheme);
    for (const key of Object.keys(a)) {
      if (!b[key]) {
        console.log(`[${scheme}] ${key}: omitido (no está en la candidata)`);
        continue;
      }
      for (const p of Object.keys(a[key])) {
        if (a[key][p] !== b[key][p]) {
          console.log(`[${scheme}] ${key}.${p}: referencia=${a[key][p]} candidata=${b[key][p]}`);
          diffs++;
        }
      }
    }
  }
  await browser.close();
  console.log(diffs ? `FALLA: ${diffs} diferencias` : 'OK: sin diferencias');
  process.exit(diffs ? 1 : 0);
})();
