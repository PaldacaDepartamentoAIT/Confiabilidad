# Formato de hallazgos

```markdown
## Hallazgos de clarificación: <feature>
Modo: feature nueva | tras un cambio

### C-01 [Alta | Media | Baja] <pregunta concreta al usuario>
Afecta a: RF-00X | P-0X
Tipo: ambigüedad | contradicción | caso límite ausente | no verificable | conflicto con la constitución
Por qué es un problema: <una o dos frases>
```

Gravedad:
- **Alta**: sin resolverlo no se puede diseñar ni implementar correctamente.
- **Media**: se puede avanzar, pero probablemente obligará a rehacer trabajo.
- **Baja**: mejora la precisión, pero no bloquea.
