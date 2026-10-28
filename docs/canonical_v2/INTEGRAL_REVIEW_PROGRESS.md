> Registro histórico del borrador `4f10480`. La continuación está documentada en
> [INTEGRAL_OFFLINE5.md](INTEGRAL_OFFLINE5.md); estos conteos no describen la edición final.

# Revisión integral: trabajo pendiente, no cierre del Corpus V2

La versión `2.0.0-offline.5-review` es un **borrador de anotación**. No sustituye
los resultados históricos de offline.4 y no constituye la entrega final pedida.
El compilador `training.integral_v2.build` permite reconstruir expedientes y
referencias completas desde originales y adjudicaciones privadas independientes.
No convierte propuestas automáticas en fichas aprobadas. No es todavía el runner
integrado de entrenamiento/evaluación requerido para cerrar el plan.

Estado local de esta revisión:

| Destino | Ítems |
|---|---:|
| Inventario reconciliado | 120 |
| Referencias completas con revisión técnica asistida | 18 |
| Cuarentena documental motivada | 9 |
| Revisión integral sin cerrar, excluida de entrenamiento | 93 |

Las ocho anomalías históricas se conservan con decisiones individuales. Se añade
una profundidad malformada que tampoco se repara por intuición. Los 93 expedientes
pendientes **no se presentan como comercialmente irresolubles**: falta completar
su anotación y adjudicación. No son gold humano ni ejemplos supervisados completos.

Las referencias cerradas cubren siete pisos, tres zócalos, tres poltronas, dos
veladores, dos closets y una mesa circular. Conservan literal completo, spans,
campos comerciales y técnicos, decisiones de ausencia, hechos con offsets locales
y absolutos y reglas. El precio, las cantidades y las unidades tienen evidencia
propia; el espesor del mesón y de las patas se mantiene en ámbitos diferentes.
Los documentos, las adjudicaciones y los artefactos derivados son privados.

## Integridad y límites de los controles

Una adjudicación congelada vincula literal, entidades, referencias comerciales,
checklist, cobertura y decisiones mediante un manifiesto separado de certificados.
Una mutación de entidad, relación, cantidad, precio o decisión no puede reutilizar
el certificado anterior. Los controles adicionales rechazan referencias huérfanas,
conjuntos vacíos, cantidades comerciales sin entidad correspondiente, derivaciones
monetarias no autorizadas, errores de alineación y firmas humanas ficticias.

**Un certificado de integridad no demuestra corrección lingüística ni comercial.**
La cobertura de caracteres registra qué texto se revisó; tampoco prueba por sí
sola exhaustividad de entidades. La adjudicación asistida debe contrastarse con
el literal, y quedan pendientes controles adversariales más amplios y la revisión
de todos los casos resolubles. No se comunica este borrador como corpus homologado.

El tokenizador experimental separa signos y unidades pegadas; se exporta junto
al bundle y no modifica `src/`, el runtime V15 ni su tokenizador. Las particiones
unen variantes numéricas y similitudes textuales transitivas entre fuentes antes
de asignar grupos. Esto es evaluación interna de documentos conocidos; no acredita
independencia externa ni elimina por sí solo toda similitud semántica de plantilla.
El pequeño conjunto cerrado actual carece de test interno: no habilita evaluación
final o entrenamiento integral. El manifiesto mantiene `training_ready=false`.

## Reconstrucción privada

Con originales, adjudicaciones y certificados accesibles localmente:

```bash
umask 077
uv run --locked python -m training.integral_v2.build \
  --sources "$PROFORMAS_SOURCE" "$CHAIRS_FLOORS_SOURCE" "$CHAIR_CATALOGUE_SOURCE" \
  --adjudications "$PRIVATE_ADJUDICATIONS" \
  --certificates "$PRIVATE_CERTIFICATES" \
  --output "$NEW_PRIVATE_OUTPUT"
```

Usar una salida nueva en `~/Descargas/`. No sobrescribir entregas ni experimentos
anteriores. El compilador rechaza salidas existentes y ubicaciones dentro de Git;
exporta DocBin por split y verifica su reimportación. El directorio resultante
contiene todos los expedientes, incluso exclusiones y decisiones pendientes.
El contenido privado nunca debe agregarse a Git ni pasarse a herramientas externas.

## Trabajo que sigue requerido

Cerrar las 93 fichas pendientes; revisar adversarialmente la coherencia completa de
las referencias; ampliar casos orales genuinamente distintos con sus relaciones;
completar la matriz de cobertura y contaminación, seleccionar grupos con dev y
holdout no vacíos, integrar el ensamblado comercial y el runner, ejecutar los diez
entrenamientos nuevos y la comparación comercial contra V15, y comprobar toda la CI.
No se han ejecutado esos entrenamientos en esta versión ni se atribuyen a ella
métricas de offline.3/4. RULES_ONLY y V1 continúan intactos.
