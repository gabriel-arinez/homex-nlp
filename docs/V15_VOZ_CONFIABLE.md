# Voz confiable v15 — alcance y validación

Base: PR #32, 4dc3f2532e8a7e406fe63986bab01669682287fe. Paquete
0.1.15, RULES_ONLY, reglas prf04-rules-v15. Contrato 1.0 sin cambios.

## Causas y cambios

- Precio: un marcador ASR degradado seguido de decimal con punto (una o dos
  cifras decimales) exige revisión INVALID_PRICE. El candidato conserva el
  literal como UNRESOLVED y el precio queda vacío. No se infiere 8500, 8050
  ni ninguna escala. Precio unitario explícito, coma decimal, miles completos,
  monedas y total negociado conservan las reglas anteriores. Es protección
  acotada de incertidumbre, no validación económica por umbral ni recuperación ASR.
- Piezas: vocabulario literal de repisas, divisiones, cubiertas, paneles, patas,
  papeleros y archivadores. Cantidades internas mantienen evidencia por pieza.
- Accesorios: ruedas, tiradores, cerraduras/chapas y soporte lateral para CPU;
  terminaciones PVC con puntos conservadas. La frontera entre accesorios evita
  absorber rieles dentro de «cajones con rieles» y perderlos al deduplicar piezas.
- Colores compuestos completos; no-gal normaliza a nogal sin cambiar offsets.
  Una mención «color madera clara» no crea MATERIAL madera de otra pieza.
- Restricciones literales de piezas/chapas se conservan en observations, además
  del rechazo de evidencia negada y de descripcion_original en el consumidor.
- Dimensiones con «profundidad de cubierta» referencian la pieza explícita.
  «Dos lados de ...» exige revisión geométrica y no completa el largo global.
- Se conservan las regresiones 0.1.14 de unidad ausente, entidad desconocida
  («etapa»), espesores contradictorios y rectificación dimensional segura.

## Evidencia y límites

La línea base en el commit #32 pasó 392 pruebas. La evidencia privada, matriz
por las 25 capturas, replays antes/después y logs se guardan fuera de Git en
~/Descargas/HOMEX_VOICE_NEXT_20261027/. No son GOLD ni datos de entrenamiento.
Las nuevas pruebas son textuales y sintéticas; no acreditan escucha humana.
No se calcula WER, precisión, recall ni F1 del piloto.

La igualdad de texto enlaza capturas 6–19 con registros ASR 01–14; captura 20
repite el texto del registro 14, 21–23 coinciden con 15–17 y 24–25 con 19–20.
El registro 18 no tiene igualdad exacta. No demuestra identidad de audio de
los intentos. No asumir correspondencia posicional ni corregir precio desde ella.

El contrato Component no ofrece padre-hijo: cajonera/cajones permanecen piezas
independientes con texto original; no se fabrican árboles ni multiplicaciones.
No se recuperan palabras ausentes o corruptas («terrar», «reales deles cópicos»,
«tableras», «estruptura»). Requieren revisión humana del original/audio.
Espesores generales siguen pendientes de componente. El catálogo no contiene
velador, atril o recepción: deben permanecer sin resolver si no hay valor activo
exacto. No se agregan migraciones ni perfiles inventados.

## Reproducción

Desde el worktree independiente: `uv sync --locked --extra dev`, `make check`,
`make distribution-check`. Los esquemas exportados deben permanecer idénticos.
Repetir replays mediante ExtractionRequest con texto original, BOB y request_id
único. No importar datos del piloto a corpus ni cambiar sus splits.

Respecto del Plan Maestro/Corpus V2 #31: mejora el motor A y la seguridad de
proyección; no cierra las etapas de GOLD, consentimiento, corpus oral revisado,
evaluación externa, NER/híbrido ni promoción. PR #31 no se fusiona ni reutiliza
como evidencia de exactitud de v15.
