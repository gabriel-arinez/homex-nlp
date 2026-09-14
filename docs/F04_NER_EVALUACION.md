# F04 — NER personalizado y evaluación híbrida

Se convirtió exclusivamente `homex_original_v1` a DocBin con la partición F02:
138 documentos train, 30 dev y 32 test. El catálogo de sillas queda excluido.
La configuración spaCy CPU se generó en `training/configs/ner-v1.cfg` y se
entrenó 50 pasos con seed/configuración de spaCy por defecto. Los artefactos
locales están bajo `artifacts/f04/` y no se versionan.

El modelo `model-best` alcanzó en dev P=0.2800, R=0.1522 y F1=0.1972; el test
sellado, evaluado una vez después de congelar esa corrida, obtuvo P=0.1949,
R=0.1030 y F1=0.1348. Solo ANCHO, ACCESORIO y PRECIO_TOTAL tuvieron señal; las
restantes etiquetas no lograron F1 distinto de cero en esta corrida.

Por tanto, el modelo no se promueve ni se presenta como mejora frente a reglas.
El motor activo continúa siendo `RULES_ONLY`; F04 entrega la infraestructura de
conversión/evaluación y evidencia reproducible. Antes de un nuevo entrenamiento
se requiere ampliar y revisar anotaciones, en especial PRODUCTO, cantidad,
espesores, dimensiones y etiquetas de apoyo de sillas, sin reabrir el test.

Reproducir la preparación local:

```bash
uv run python -m training.convert_to_docbin data/curated/homex_original_v1.jsonl data/splits/homex_original_v1.json artifacts/f04/corpus
uv run python -m spacy train training/configs/ner-v1.cfg --paths.train artifacts/f04/corpus/train.spacy --paths.dev artifacts/f04/corpus/dev.spacy --output artifacts/f04/model --training.max_steps 50 --training.eval_frequency 25 --gpu-id -1
uv run python -m training.evaluate_ner artifacts/f04/model/model-best artifacts/f04/corpus/test.spacy
```
