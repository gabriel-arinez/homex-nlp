# AP1 — Detección de secretos en CI

**Corte:** 2026-10-12. **Alcance:** complemento incremental del gate existente.

## Brecha verificada

En `main` se ejecutan lint/ruff, pruebas, esquemas, corpus, contratos, distribución y runtime NLP. Sin embargo, el workflow no ejecutaba detección automatizada de secretos; `homex-deploy` ya emplea `gitleaks/gitleaks-action@v2`.

## Ajuste

Se incorporó el job `secrets` al workflow existente, sobre el historial Git completo (`fetch-depth: 0`) y con `GITHUB_TOKEN` de lectura. No se añade infraestructura ni credenciales externas, ni se modifica el paquete comercial.

## Criterios

- Una filtración real obliga a revocar/rotar el secreto y a tratar el incidente; no ignorar hallazgos sólo para aprobar CI.
- Las credenciales ficticias en fixtures, si generasen alerta, requieren una excepción mínima y justificada; nunca desactivar indiscriminadamente el detector.
- La nueva comprobación sólo será exigible por GitHub tras configurar reglas de protección de `main` con permisos de administración.
- No se alteraron suites existentes ni se promovió RC2/D07 a producción.

Verificación remota obligatoria: nuevo job `secrets` en el PR, además de los jobs existentes, con resultados visibles antes de integración.
