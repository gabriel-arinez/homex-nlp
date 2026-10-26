# Corpus HOMEX 2.0.0-rc.1 — base y fuentes

Candidato pasivo, fecha de decisión 25/10/2026 America/La_Paz. No activado.
Base comprobada NLP `45404c6580ae2d488b338c46ba63689feccb3501`, paquete 0.1.11,
reglas v12, RULES_ONLY, contrato NLP 1.0. PR #19 abierto draft; main no se asumió base.
Rama exclusiva `feat/prf04-corpus-v2-candidato-20261025`; worktree nuevo aislado.
Checkout local original NLP `449a5cf`, Backend `8f6fed352e8e49f819884e9db7ffb1d24f355ca7`,
Frontend `554f382e40533ed16c462c9048482c487e603aad`, todos conservados.
Backend remoto abierto más reciente consultado: PR #35, `86da72ef25377e4a65d9176c655678b29cdf4cd4`, v11.
No se presume integración Backend v12. El checkout Backend tiene un archivo temporal no seguido:
no se añadió, abrió ni modificó. Estados y lista completa de worktrees quedan en evidencia privada.

Consumidores actuales fijan las rutas V1 (`training/corpus.py`, `train_prf04.py`,
`compare_prf04.py`, `evaluate_structured_prf04.py`, Makefile y tests).
Este candidato tiene una única raíz nueva y consumidores explícitos `training.corpus_v2.*`.
Ningún consumidor V1 se cambió. V1: 380/101/97/97, total 675; 300 IDs de proforma sintética,
65 familias de ejemplos; 483/94/98 train/dev/test históricos. No son 300 cotizaciones reales.
Los hashes completos antes/después están en `07_SPLITS_Y_MANIFIESTOS_V2/baseline_v1_sha256.json`.

Se leyeron encargo vigente, continuidad, plan histórico, tres TXT y políticas/código vigentes.
El encargo vigente sustituye las pausas entre etapas del plan histórico.

| Fuente privada | Bytes | Líneas | SHA-256 |
|---|---:|---:|---|
| PROFORMAS.txt | 40007 | 378 | `f9497615494ba59c8b76c79c21c5411bbc919aa895c1eff2cc70c88bec0b8020` |
| SILLAS-PISOS-OTROS.txt | 7344 | 96 | `8e22fc29be4d2ed1d75d9745409df02c24cd953bca25a79dc06c083a77fd7ca0` |
| inventario de sillas.txt | 6933 | 20 | `43417573bc0ec98b90d63de89bd9b7dab236760724bbe74377a03fd63d4a0089` |

Los tres originales se preservan byte por byte con permisos privados en el bundle.
Son documentos comerciales; no audio. Inventario privado: 79 ítems candidatos de PROFORMAS,
22 de SILLAS-PISOS-OTROS y 19 fichas de catálogo, total 120. Un título separado de su descripción
por un blanco se une manteniendo ambos bloques fuente. No consta ID verificable de proforma real:
se mantiene null. Se conserva cada rango de bytes/caracteres/líneas y su hash.

Faltantes tras buscar nombres en directorios accesibles: piloto histórico de 48, su script y
`homex-auditoria-1b-675-20261024-224839.json`. No se reconstruyen desde la nota histórica.
Existe un informe antiguo de corpus distinto; no acredita aquella auditoría 1B.
No se obtuvo audio humano ni anotación comercial humana independiente.
