# Corpus integral V2 offline.5.1

Esta ejecución continúa el cierre del PR #37. La revisión de anotación final es
`2.0.0-offline.5.1`: corrige 16 escalares con eje conocido y unidad ausente, y
cuatro expresiones multiextensión con eje explícito. Se preservan las corridas
anteriores; no se reutilizan sus métricas como resultados finales. El valor sin
unidad conserva `unidad=null` y no hereda metros de otra dimensión. Los controles
rechazan ahora la omisión de estas entidades incluso si se vuelve a sellar una
adjudicación incorrecta.

Sustituye el borrador
`offline.5-review` únicamente para el alcance offline; no promueve modelos ni
modifica V15/RULES_ONLY. Los originales y los 675 registros históricos V1,
incluidos sus 98 test, permanecen inmutables.

Las adjudicaciones privadas cubren 120 bloques: 108 fichas completas aptas para
supervisión técnica asistida y 12 cuarentenas con evidencia individual. No quedan
fichas con revisión pendiente. Las cuarentenas conservan las ocho anomalías
históricas, una profundidad malformada y tres diámetros estructurales sospechosos.
No se corrigen unidades por intuición. Los atributos resolubles se conservan en
los expedientes; el bloque ambiguo completo no se usa como NER supervisado.

Hay 53 casos orales sintéticos nuevos, explícitamente redactados y anotados por
el agente. No son grabaciones reales, transcripciones humanas ni el piloto
histórico de 48 frases. Algunos son subconjuntos documentales; las condiciones
comerciales nuevas se identifican como sintéticas. Ningún caso se presenta como
paráfrasis íntegra si omite atributos. Se conservan padre, hash, transformación,
secuencia de cancelación/rectificación y grupo; una referencia oral puede emplear
hechos verificables de un bloque en cuarentena sin trasladar su campo conflictivo.

Cada adjudicación separa NER y referencia comercial PRF-03, con offsets locales y
absolutos, hechos por path, normalizaciones, ausencias y conflictos. Los spans de
material, espesor y dimensiones deben concordar con sus hechos; no se acepta el
sufijo de una cifra como evidencia de otra. La cobertura distingue entidades de
contexto revisado. Certificados separados detectan alteraciones; acreditan la
integridad de una revisión asistida, no infalibilidad comercial ni gold humano.
Las ambigüedades de ámbito/unidad se excluyen del campo correspondiente y no se
resuelven por proximidad. Se conservan las 24 etiquetas efectivas; cantidades
internas y conjuntos se transportan como evidencia auxiliar del DTO existente.

El generador agrupa padres, múltiples padres, duplicados numéricos y plantillas
antes de asignar splits. La cobertura de etiquetas raras se asegura moviendo
grupos completos a train, antes de observar modelos o resultados. Compara texto normalizado (umbral 0,80) y esqueletos de
anotación largos (0,85), uniendo transitivamente sus familias. El holdout se llama
`HOLDOUT_INTERNO_DE_DOCUMENTOS_CONOCIDOS`: no es externo, ciego ni gold humano.
Las 27 observaciones sintéticas históricas, incluidos sus 16 muebles, se evalúan
aparte y nunca entran al nuevo train. No se predice sobre el test V1.

El ensamblador experimental conserva negaciones y rectificaciones, separa cantidad
comercial/interna, mantiene ámbitos por componente y no selecciona valores
incompatibles. Distingue precio unitario, total negociado y descuento; una referencia
unitaria de un total solo se calcula con descuento cero explícito y división exacta
a centavos. No convierte moneda ni infiere ejes/unidades ausentes. El backend real
se verifica estructuralmente desde funciones puras de su revisión V15 fijada,
sustituyendo únicamente la clase de excepción; no se importan servicios Django,
no se consulta la base de datos y no se despliega ningún adaptador nuevo.

El protocolo conserva semillas 404/405, 25 épocas máximas, mínimo 8, paciencia 6,
batch 8 y dropout 0,2. D1 usa V1 train intacto; D2 fichas documentales; D3 oral nuevo;
D4 mezcla natural y D4W duplica el muestreo oral para compensar la longitud de las
fichas. El checkpoint se selecciona con dev y se congelan los diez antes de abrir
el holdout. F1 bruto y candidatos ACCEPTED se reportan separados. La evaluación
estricta de relaciones y atributos completos es distinta del comparador histórico
de los 16 casos; ambos se conservan para no atribuir mejoras a un cambio de métrica.

## Reproducción privada

```bash
GITLEAKS_BIN=/ruta/al/gitleaks \
BACKEND_PRF03_GIT=/ruta/al/backend-con-revision-V15 \
bash tools/run_integral_offline5.sh \
  "$ORIGINAL_PROFORMAS" "$ORIGINAL_SILLAS_PISOS" "$ORIGINAL_CATALOGO" \
  "$ADJUDICATIONS" "$CERTIFICATES" "$ORAL_REVIEWS"
```

Ejecutar desde el worktree autorizado limpio. El runner crea una salida única en
`~/Descargas/`, restringe permisos, compila dos veces, compara hashes, valida,
reimporta DocBin, ejecuta checks/auditorías, entrena y evalúa. El escaneo Git cubre todos los
commits del PR desde `origin/main`, sin nuevas exclusiones de secretos. Una falla detiene el
proceso y devuelve FAIL: el cuerpo corre en otro Bash con `errexit`, evitando que
un condicional externo suprima ese control. Rechaza destinos existentes; no
sobrescribe offline.3/4 ni el borrador anterior. Reconstruir requiere los tres
originales y los tres archivos privados de anotación. No subirlos a Git/CI.

Los resultados cuantitativos de esta corrida se publicarán como agregados,
separados de las métricas históricas. No se atribuyen resultados a entrenamientos
que todavía no hayan concluido. La homologación humana, voz real/WER y una nueva
fuente externa son controles distintos y no se afirman por esta ejecución técnica.
