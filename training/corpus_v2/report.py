"""Deterministic documentation and coverage tables for the opt-in candidate."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from training.corpus_v2.build import DEFAULT, MANIFEST, refresh_hashes, table


def report(out=DEFAULT):
    counts = json.loads((out / MANIFEST / "coverage.json").read_text())
    records = [
        json.loads(line)
        for folder in ("04_CORPUS_DOCUMENTAL_V2", "05_CORPUS_ORAL_V2")
        for path in sorted((out / folder).glob("*.jsonl"))
        for line in path.read_text().splitlines()
    ]
    fingerprints = json.loads(Path("training/corpus_v2/source_fingerprints.json").read_text())
    (out / MANIFEST / "source_fingerprints.json").write_text(
        json.dumps(fingerprints, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    )

    def md(name, text):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.strip() + "\n")

    source_table = "\n".join(
        f"| {s['file']} | {s['bytes']} | {s['lines']} | `{s['sha256']}` |" for s in fingerprints
    )
    md(
        "00_ESTADO_BASE_Y_FUENTES.md",
        f"""
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
Los hashes completos antes/después están en `{MANIFEST}/baseline_v1_sha256.json`.

Se leyeron encargo vigente, continuidad, plan histórico, tres TXT y políticas/código vigentes.
El encargo vigente sustituye las pausas entre etapas del plan histórico.

| Fuente privada | Bytes | Líneas | SHA-256 |
|---|---:|---:|---|
{source_table}

Los tres originales se preservan byte por byte con permisos privados en el bundle.
Son documentos comerciales; no audio. Inventario privado: 79 ítems candidatos de PROFORMAS,
22 de SILLAS-PISOS-OTROS y 19 fichas de catálogo, total 120. Un título separado de su descripción
por un blanco se une manteniendo ambos bloques fuente. No consta ID verificable de proforma real:
se mantiene null. Se conserva cada rango de bytes/caracteres/líneas y su hash.

Faltantes tras buscar nombres en directorios accesibles: piloto histórico de 48, su script y
`homex-auditoria-1b-675-20261024-224839.json`. No se reconstruyen desde la nota histórica.
Existe un informe antiguo de corpus distinto; no acredita aquella auditoría 1B.
No se obtuvo audio humano ni anotación comercial humana independiente.
""",
    )
    labels = json.loads(Path("data/manifests/prf04_labels.json").read_text())["labels"]
    md(
        "03_GUIA_ANOTACION_V2.md",
        f"""
# Guía nueva del candidato V2

La guía operativa V1 sigue intacta. Etiquetas NER exactas (24): {", ".join(labels)}.
`CANTIDAD_INTERNA` es una relación semántica; NO es una etiqueta NER permitida.
Orígenes, revisión y fenómenos son metadatos, nunca clases NER nuevas.

Offsets sobre Unicode Python sin normalización, intervalos `[start,end)`, texto literal y hash.
Spans ordenados, sin solapes; spaCy español debe aceptar `char_span(..., alignment_mode="strict")`.
Un material/espesor/color/acabado pertenece al componente delimitado por evidencia, sin propagación.
Tablero de 18 mm y mesón de 27 mm son dos afirmaciones distintas. Nombre/cantidad interna de
cajones no equivale a dos cajoneras; las relaciones conservan el objetivo correcto.
`una mesa central y dos laterales` no incrementa la cantidad comercial del juego.
`para diez personas` es capacidad, no diez mesas. Se permiten OBSERVACION para la frase contextual
y relaciones auxiliares para conteos, sin inventar NER. Sin datos no se completa cantidad.

Precio unitario, total explícito y descuento de línea se distinguen por contexto literal.
Decimal preserva centavos. Solo total inequívoco + cantidad conocida + descuento explícito cero
+ división exacta permite `derived_unit_price`. Descuento ausente se mantiene null: no autoriza
una derivación. Para V1, una ecuación total=unitario*cantidad sin descuento escrito comprueba
consistencia de importes explícitos; no afirma una declaración de descuento cero.
Moneda mencionada queda literal; moneda de Condiciones ausente no se inventa ni se convierte.
Un número sin modalidad de precio se conserva como observación y no se vuelve unitario.

`a elección`, `por confirmar`, `según diseño` expresan pendientes; no COLOR positivo.
En rectificaciones la primera afirmación reemplazada se marca OBSERVACION; la nueva conserva su
entidad y la decisión semántica explicita el reemplazo. En negaciones no se acepta el atributo negado.
En anáforas solo se resuelve un antecedente explícito único. Ante falta de antecedente queda null.
Para dos productos independientes y cancelaciones se espera ABSTAIN y ninguna propuesta fusionada.
Las dimensiones sin eje/unidad y unidades sospechosas se conservan literalmente, sin corregir 40 m
ni 80mts. La investigación no habilita voz UI para sillas/pisos/otros.

Sillas sin código verificable no reciben SKU; código ficticio de estrés se declara no confirmado.
Pisos: M2 decimal; zócalos: BARRA, distinto de largo físico 2,44 m. No convertir metros a barras.
Catálogo y cotización negociada tienen contextos distintos y fechas que pueden no constar.

Cada referencia lleva hechos con evidencia exacta, componentes/atributos y calidad de revisión.
V1: auditor literal con gramática explícita, independiente de spans/expected V1 y del runtime;
esto no es una segunda anotación humana ni independencia estadística del conjunto de prueba.
Nuevos: recetas semánticas explícitas escritas antes de renderizar NER. Tests de mutación usan
fixtures propios y comprueban cantidades, negaciones, ámbitos, precios y preservación de datos.
Las referencias tienen cobertura comercial/relacional declarada; los atributos de catálogo son
literales de investigación, no todos campos técnicos normalizados. No afirmar gold humano.

Cada registro incluido tiene referencia y procedencia; todo documento privado sin homologación
permanece en cola, incluidos cuatro ejemplos documentales parciales de las cuatro familias.
`REQUIRES_REVIEW` es una salida técnica revisable; `REQUIERE_REVISION_HUMANA` en cola documental
impide usar datos comerciales dudosos como supervisión. Los estados no se añaden a contratos API.
PRF-03 mantiene 10 conjuntos/40 componentes, atributos, accesorios y descripción original.
`schema_version=1.0` pertenece al contrato NLP; no al JSONB comercial `datos_tecnicos`.
""",
    )
    md(
        "08_VALIDADORES_Y_TESTS_V2/README.md",
        """
# Implementación única y comandos opt-in

Código versionado en `training/corpus_v2/`: `build.py`, `semantic.py`, `validate.py`,
`record.schema.json`, `recipes.json`, `private_ingest.py`, `verify_private.py`, `docbin.py`,
`report.py`, `reproduce.py`, `reconcile.py`. Tests independientes en `tests/training/test_corpus_v2.py`.
Este índice no duplica las implementaciones.

```bash
uv sync --locked --extra dev --python 3.11.15
uv run --locked --extra dev python -m training.corpus_v2.reproduce --output /tmp/homex-v2-rebuild
uv run --locked --extra dev python -m training.corpus_v2.validate /tmp/homex-v2-rebuild
uv run --locked --extra dev pytest tests/training
uv run --locked --extra dev python -m training.corpus_v2.docbin /tmp/homex-v2-rebuild /tmp/homex-v2-docbin
make corpus-check docbin-check
```

No se ejecuta train_prf04 ni se sustituye V1. Para experimentar después de homologación,
seleccionar esta raíz explícitamente y diseñar un consumidor opt-in; los consumidores actuales
siguen fijados a V1. No copiar este candidato sobre data/corpus, expected o splits.

Privados, fuera de Git: `private_ingest --sources <tres TXT> --output <directorio privado fuera de Git> --review-recipes <recetas privadas>`
y `verify_private <directorio privado>`. El ingestor rechaza un destino dentro de un checkout.
Conservar permisos 700/600. El script verifica bytes originales, rangos, cobertura de cada carácter
no blanco y exclusión de originales de supervisión. No imprime textos comerciales.
""",
    )
    md(
        "10_PENDIENTES_REVISION_HUMANA.md",
        """
# Cola humana y limitaciones

1. Homologación comercial global de 727 referencias técnicas, incluidas las 675 heredadas.
   No se obtuvo revisor humano ni doble anotación. Ningún registro se denomina gold humano.
2. Los 120 ítems documentales privados quedan excluidos de entrenamiento y test supervisado;
   nueve presentan anomalías localizadas: unidades 40m/80mts, mesón 0.50 Cm, número 0,3.6 y
   unitario/total discrepantes con cantidad ausente. No se impone corrección.
   Detalle con evidencia original, bloques, líneas y alternativas en private/document_quarantine.jsonl.
3. Cuatro referencias privadas documentales de las cuatro familias son parciales, no gold,
   y siguen en quarantine. No se publican precios negociados ni textos comerciales nuevos.
4. Resolver autorización/homologación de TXT antes de incorporar muestras documentales públicas.
   Los códigos compartidos con catálogo conservan sus precios de origen y fecha desconocida.
5. Recuperar piloto oral histórico de 48 y JSON 1B si se quiere cerrar la identidad de los 80 prefijos.
   El detector actual reproduce 34 señales y 79 grupos; no se falsifica el contador 80.
6. Recabar audio autorizado y referencias humanas para test externo independiente. No hay WER.
7. Para entrenamiento útil adicional, adquirir nuevas fuentes independientes: los 675 V1 forman
   un componente conectado con test histórico y no se desarma para inflar train.

Las tablas exportables públicas contienen la homologación global. Las tablas privadas incluyen
cada ítem pendiente y cada anomalía, con literal y alternativa de revisión; nunca se usan como gold.
""",
    )
    breakdown = Counter(
        (r["category"], r["origin"], r["style"], r["split"], r["example_kind"]) for r in records
    )
    table(
        out / MANIFEST / "coverage_by_family_origin_style_split.csv",
        [
            dict(zip(("family", "origin", "style", "split", "kind"), key)) | {"records": n}
            for key, n in sorted(breakdown.items())
        ],
    )
    phen = defaultdict(Counter)
    for r in records:
        for p in r["phenomena"]:
            phen[p][r["example_kind"]] += 1
    table(
        out / MANIFEST / "phenomena_positive_negative_ambiguous.csv",
        [
            {
                "phenomenon": p,
                "positive_synthetic": c["POSITIVO_SINTETICO"],
                "positive_partial": c["POSITIVO_PARCIAL"],
                "negative": c["NEGATIVO"],
                "ambiguous": c["AMBIGUO"],
                "denominator_records": len(records),
            }
            for p, c in sorted(phen.items())
        ],
    )
    family_table = "\n".join(
        f"| {family} | {n} |" for family, n in sorted(counts["families"].items())
    )
    md(
        "11_COBERTURA_Y_CALIDAD_V2.md",
        f"""
# Cobertura y calidad declarada

727 incluidos: 675 V1 + 12 bases documentales sintéticas nuevas + 40 orales sintéticos nuevos.
687 documentales sintéticos, 40 orales. Estados V1: {json.dumps(counts["v1_states"], ensure_ascii=False)}.
Correcciones sin cambiar texto: descuentos explícitos en expected, relaciones de cantidad interna,
capacidad separada, y 56 spans de accesorio ampliados a incluir el núcleo «Membrana protectora».
Los 375 CORREGIDO pueden tener varias causas; no sumarlas como registros distintos.
Los 300 APROBADO_SIN_CAMBIO conservan la semántica principal; el envoltorio V2 y su evidencia son nuevos.

| Familia | Incluidos |
|---|---:|
{family_table}

38 train / 12 dev / 677 test. Los 675 V1 se conectan por uniones transitivas de proforma,
familia, plantilla enmascarada y prefijo. Al contener test histórico, prevalece test para todo
el componente. No se entrenó sobre ese grupo. Los 52 nuevos se agrupan por caso base y familia
semántica, sin cuotas artificiales: muebles/pisos de desarrollo de datos van a train, sillas/otros
a dev y dos negativos fuera de alcance a test. No hay variantes orales de casos V1 test.
La semilla declarada 20261025 identifica el plan determinista; no hay sorteo aleatorio ni ratio objetivo.
Este test retrospectivo fue leído al auditar; no es ciego ni humano externo. Queda sellado para
entrenamiento a partir de este candidato, y no se evaluó un motor para seleccionar cambios.
Los tamaños no sostienen aún una comparación representativa entre modelos; no ocultar esta limitación.

34 señales históricas reconstruidas: falsos positivos como exigencia de etiqueta NER inexistente,
con relaciones internas explícitas confirmadas y registradas. 79 grupos de prefijos entre particiones
V1; riesgo de plantilla confirmado, no 79 copias de documentos. 39 pares con Jaccard de 4-gramas >=0.50,
todos tratados dentro de partición. El validador recalcula pares entre splits; cero riesgos conocidos
sin tratar con esos detectores. No es demostración universal de ausencia de similitud semántica.
No hay duplicados exactos. Las tablas de grupos/pares y decisiones son parte del manifiesto.

24 etiquetas presentes, {len(counts["phenomena"])} fenómenos declarados (ver CSV, conteos por denominador 727).
La cobertura de fenómenos no es una estimación de frecuencia de vendedores.
Tipos: {json.dumps(counts["example_kinds"], ensure_ascii=False)}.
Vocabulario regional, perturbaciones ASR y oralidad son sintéticos explícitos.
Piloto antiguo 48 no encontrado, 0 incorporados desde ese piloto.

Trazabilidad interna: 727/727 texto→fuente/receta→NER→expected→grupo→split.
Correspondencias auténticas V1 confirmadas: 0/675; no se certifican por compartir título.
Privados: 120/120 ítems con archivo/hash/bloque/líneas/bytes; 4 ejemplos parciales con vínculo literal.
Vínculos documentales se validan en el bundle, fuera de Git. No atribuir los 727 a cotizaciones reales.
Voz humana, ASR real, anotación humana independiente y test externo humano: 0.
""",
    )
    md(
        "12_EVIDENCIAS_REPRODUCIBILIDAD.md",
        """
# Reproducción y evidencia

Entorno: Python 3.11.15, spaCy 3.8.13; dependencias del uv.lock base sin cambios.
Resultados ejecutados en ese entorno (repetidos en el cierre):

| Comando/control | Resultado |
|---|---|
| `pytest -q` | 277 aprobadas, incluye 26 pruebas V2 |
| `pytest tests/training` | 43 aprobadas al cierre |
| `make corpus-check docbin-check` | cuatro corpus V1 válidos; 675 DocBin V1 |
| `corpus_v2.validate` | 727/727 registros y referencias, cero errores |
| `corpus_v2.docbin` | 727/727 roundtrip, sin entrenamiento |
| `ruff check` y `ruff format --check` | aprobados |
| `export_schemas.py --check` | aprobado |
| dos reconstrucciones limpias | mismos bytes y hashes |
| V1, runtime y consumidores protegidos | hashes y diff sin cambios |
| `verify_private` | 3/3 originales, 120 ítems, 4 parciales, cero supervisados |
| `git diff --check` | aprobado |

La evidencia detallada de comandos, códigos de salida, entorno y hashes se entrega bajo evidence/
en el bundle privado. Las pruebas registradas se ejecutaron sobre este candidato, no se predicen.

```bash
uv run --locked --extra dev python -m training.corpus_v2.reproduce --output /tmp/homex-v2-rebuild-a
uv run --locked --extra dev python -m training.corpus_v2.reproduce --output /tmp/homex-v2-rebuild-b
uv run --locked --extra dev python -m training.corpus_v2.validate /tmp/homex-v2-rebuild-a
uv run --locked --extra dev pytest -q
make corpus-check docbin-check
uv run --locked --extra dev ruff check src tests tools training
uv run --locked --extra dev ruff format --check src tests tools training
uv run --locked --extra dev python tools/export_schemas.py --check
git diff --check
```

La reconstrucción de datos/documentación es determinista. Hashes en sha256.json cubren exactamente
los archivos del candidato salvo ese propio manifiesto. baseline_v1_sha256.json fija todos los
archivos V1, incluidos expected/splits/manifiestos. Las fechas de ejecución y resultados de comandos
se separan del dataset para no alterar sus hashes. Dos reconstrucciones desde cero deben coincidir
byte por byte con el candidato. No se entrena, evalúa RULES_ONLY en test ni mide WER.

El workflow base entrena NER y construye paquetes automáticamente en push/PR.
Este encargo prohíbe entrenamiento: los commits de publicación llevan [skip ci] para no dispararlo.
No se modifica el workflow; verificación local sí ejecutada, CI remoto de este candidato no afirmado.
No se construyeron wheels nuevos por este trabajo. PR solo draft, sin merge ni despliegue.
""",
    )
    md(
        "13_INFORME_FINAL_Y_HANDOFF.md",
        """
# Entrega consolidada — 2.0.0-rc.1

Cinco entregas: auditoría 675/675 y fuentes; candidato documental; corpus oral sintético;
particiones/validadores/fixtures independientes; paquete y documentación reproducible.
Artefactos 00–13 localizados en esta raíz única; implementaciones únicas indicadas en el índice 08.
Datos activos V1, runtime, reglas, wheels, lock, pyproject, APIs y consumidores permanecen intactos.
Backend/frontend se consultaron solo para lectura de contratos PRF-03/04.

Candidato técnico: 727 registros incluidos, 727 expected con evidencia, cuatro familias.
375 V1 con correcciones demostrables en anotaciones/expected, 300 sin cambio semántico principal.
12 bases documentales sintéticas nuevas, 40 frases orales sintéticas. No son audios ni piloto histórico.
En el bundle: tres originales íntegros, 120 ítems inventariados, nueve anomalías y cuatro ejemplos
reales parciales, todos privados y excluidos de entrenamiento/test supervisado.

Criterios estructurales, preservación, aritmética aplicable, offsets spaCy, trazabilidad interna y
fugas conocidas de detectores se verifican automáticamente. Homologación comercial humana,
independencia humana del gold y test externo de voz siguen pendientes y no se declaran cumplidos.
Los splits conservadores dejan 38/12/677, con todos los V1 en test retrospectivo: no vender este
candidato como dataset equilibrado o prueba de mejora de campo. No se entrenó ni se promovió motor.

Privacidad: solo sintéticos previamente autorizados, recetas nuevas y hashes de originales entran
a Git. Textos reales/precios negociados, rutas personales y diagnósticos privados quedan en bundle
con permisos 700/600. El índice del bundle identifica cada sección y su condición pública/privada.
Publicación y SHA/PR efectivos se registran en evidence/publication.json del bundle; no se atribuye
un PR hasta que exista respuesta del servicio. La rama base v12 continúa separada del frente A.

Siguiente paso del plan maestro: homologación comercial de referencias y nueva fuente independiente
para ampliar entrenamiento; después experimento controlado reglas/NER/híbrido y evaluación externa
con voz humana autorizada. No activar V2 ni reinterpretar el contrato durante este encargo.
""",
    )
    md(
        "INDEX.md",
        """
# Índice único — candidato pasivo

00 estado/fuentes; 01 auditoría CSV/JSON; 02 correspondencias; 03 guía nueva; 04 documental;
05 oral; 06 expected; 07 particiones/manifiestos/cobertura; 08 índice de herramientas/tests;
09 matriz V1→V2; 10 cola humana; 11 calidad/cobertura; 12 reproducción; 13 informe/handoff.
Esta raíz es la única fuente versionada V2. La copia del bundle es un artefacto de entrega inerte.

Los hashes de herramientas/recetas/test están en 07/tooling_sha256.json.

Los TXT, inventario de ítems, comparaciones de precios y referencias documentales parciales
se entregan exclusivamente en private/ del bundle fuera de Git. Ningún TXT real nuevo está publicado.
""",
    )
    refresh_hashes(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=DEFAULT)
    a = p.parse_args()
    report(a.output)


if __name__ == "__main__":
    main()
