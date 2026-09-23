# Plantilla: constitution.md

```markdown
# Constitución
Estado: borrador | aprobada

## P-01 <título>
<principio en una frase>
Se verifica: <mecanismo concreto: herramienta, métrica y umbral, o revisión>
```

## Ejemplos de principios bien y mal formulados

- ✗ "El código debe ser de calidad." No se puede verificar.
- ✓ "Todo el código pasa el linter sin avisos. Se verifica: `npm run lint` sin errores ni warnings en CI."
- ✗ "Tener buenos tests."
- ✓ "La cobertura de líneas es ≥ 80 %. Se verifica: informe de cobertura de `npm test -- --coverage`."
