# HOMEX — Corpus de dictados comerciales (grabaciones AAC)

**Estado:** 120 guiones de referencia listos, audios originales pendientes. No se han ejecutado evaluaciones reales de ASR/NLP ni cambiado los repositorios de HOMEX.

## Cobertura verificable

| Categoría | Registros/guiones | Carpeta |
|---|---:|---|
| Muebles a pedido | 79 | `01_muebles_pedido/` |
| Sillas | 31 | `02_sillas/` |
| Pisos flotantes | 7 | `03_pisos/` |
| Otros (zócalos) | 3 | `04_otros/` |
| **Total** | **120** | |

Fuentes: `PROFORMAS(4).txt` (80 bloques textuales = 79 registros comerciales, los bloques 68–69 son uno), `SILLAS-PISOS-OTROS(3).txt` (22 casos) e `inventario de sillas(1).txt` (19 fichas). **No eliminar los duplicados**: todos conservan su propio ID, aunque no son observaciones independientes para medir generalización. 

## Qué leer

Leer solamente el párrafo de **DICTADO** correspondiente al ID, desde `GUIONES_HOMEX_LECTURA.docx` o los archivos `MP-xxxx.txt`, `SIL-xxxx.txt`, `PIS-xxxx.txt` y `OTR-xxxx.txt` (también agrupados en los Markdown `GUIONES_*.md`). **Nunca leer los ID, títulos, notas ni instrucciones**. Si se comete un error, cancelar y volver a grabar esa toma completa. No inventar datos ausentes de las proformas; las ambigüedades están en `control/INCONSISTENCIAS_Y_DECISIONES.md`.

## Formato definitivo: AAC original; WAV compatible para ASR

Cada grabación original debe tener extensión **`.aac`**, el ID exacto y su carpeta de categoría:

```text
01_muebles_pedido/audios/MP-0001.aac
02_sillas/audios/SIL-0001.aac
03_pisos/audios/PIS-0001.aac
04_otros/audios/OTR-0001.aac
```

**Importante sobre la compatibilidad real:** el backend `apps/capturas/audio.py` y el paquete `homex-nlp` `asr/audio_validation.py` aceptan por extensión `.wav`, `.mp3`, `.m4a`, `.ogg` y `.webm`; **no aceptan `.aac` como extensión de entrada directa**. El backend conserva la extensión y la copia hacia el ASR; no se verificó conversión automática `.aac → WAV` en este recorrido. Por ello la preparación por lotes incluida en este paquete convierte cada AAC **sin alterar ni eliminar el original**. No basta con renombrar el archivo. Esta corrección es **del corpus de evaluación**, no una modificación de la aplicación. Si se desea cargar `.aac` directamente en el HOMEX productivo, Codex tendrá que implementar y probar esa compatibilidad en el backend/frontend de forma independiente.

`control/preparar_audios_asr.py` utiliza FFmpeg para generar **PCM 16 bits, mono, 16 kHz, WAV** y lo guarda en la carpeta `audios_asr/` de la categoría:

```text
01_muebles_pedido/audios_asr/MP-0001.wav
02_sillas/audios_asr/SIL-0001.wav
03_pisos/audios_asr/PIS-0001.wav
04_otros/audios_asr/OTR-0001.wav
```

Respeta el límite actual de **20 000 000 bytes** y **300 segundos**. Rechaza archivos vacíos, formatos falsamente renombrados, audio inválido, WAV demasiado grande o WAV preexistente sin procedencia íntegra. Al convertir registra `evaluaciones/conversiones.csv` con el SHA-256 de ambos archivos. No sobrescribe WAV previos silenciosamente.

## Preparación y comprobación desde Ubuntu

Descomprimir el ZIP en `~/Descargas/` conservando la carpeta superior. Una vez tengas audios:

```bash
BASE="$HOME/Descargas/HOMEX_Guiones_Evaluacion_Voz"
cd "$BASE"

# Solo si ffmpeg/ffprobe no están instalados:
sudo apt install ffmpeg

# Comprobar correspondencia de archivos AAC por ID:
python3 control/validar_audios.py --listar-faltantes --verificar-ffprobe 2>&1 | tee logs/AUDITORIA_AAC.txt

# Convertir AAC originales a WAV compatibles, sin modificar el audio original:
python3 control/preparar_audios_asr.py 2>&1 | tee logs/CONVERSION_AAC_WAV.txt

# Cuando existan las 120 grabaciones, verificar toda la cadena:
set -o pipefail
python3 control/validar_audios.py --exigir-completos --verificar-ffprobe --verificar-convertidos 2>&1 | tee logs/AUDITORIA_FINAL.txt
```

Si necesitas fallar ante grabaciones faltantes, ejecutar `python3 control/preparar_audios_asr.py --exigir-completos`.

## Contrato de asociación para Codex

1. Leer `manifiesto.csv` (UTF-8 con BOM, separador `;`), que registra por **cada ID** `ruta_audio_esperada` (AAC), `ruta_audio_compatible_asr` (WAV) y categoría.
2. Leer `referencias/guiones_referencia_pregrabacion.jsonl` (JSON Lines, UTF-8, un registro por ID): campo `guion` = **referencia escrita provisional** de lo que se leerá. No es una salida real del ASR. No leer Word como fuente automatizada.
3. Verificar 1 a 1 que el ID del AAC, el ID del WAV y el ID de la referencia coinciden. Comprobar tamaños, formato, hashes y auditoría.
4. Para el motor actual, utilizar **el WAV generado**. No pasar el AAC directamente a los validadores actuales.
5. El CLI `homex-asr` borra el audio temporal que recibe. **No pasarle jamás un archivo de esta colección como entrada directa**: Codex debe crear una **copia temporal descartable** del WAV y usar esa copia. El flujo backend crea también su propia copia para ASR y elimina temporales.
6. Guardar transcripción real de ASR y resultado NLP por ID en `evaluaciones/` con salida completa de consola en `logs/`. Hacer primer pase sin modificar las reglas actuales.
7. Antes de calcular WER, escuchar/confirmar que lo leído coincide con `guion`. Si difiere, guardar una referencia humana verificada **por separado**, sin borrar el guion fuente.
8. Comparar NLP con valores estructurados anotados y validados por humanos, no solamente contra texto de la transcripción. Comparar también la aplicación en el formulario si se prueba el flujo integral.
9. Mantener separados los ensayos de ajuste y la evaluación final; duplicados comerciales no cuentan como casos ciegos independientes.

**Catálogo:** cantidad de compra, total comercial y stock no son campos que la extracción de voz aplique automáticamente. **Muebles a pedido:** pueden dictar cantidades y precios claros según el guion. Los importes originales son históricos, no precios vigentes.

**Privacidad:** proformas y grabaciones reales **no** deben publicarse en GitHub. Mantenerlas en la carpeta local de evaluación.
