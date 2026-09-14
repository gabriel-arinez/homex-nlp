# F06 — Distribución y cierre del alcance NLP

El artefacto distribuible se construye con `uv build`. Se valida desde wheel y
sdist en un entorno aislado; los comandos `homex-nlp` y `homex-asr` son sus
interfaces locales. El paquete no instala Django, Celery, Redis, PostgreSQL ni
un modelo ASR descargado.

El futuro backend instala una versión fijada del wheel y llama a
`RulesEngine.extract(ExtractionRequest(...))`. Para HITL, el backend recupera
su propia evidencia persistida y puede usar `compare_fields` como cálculo puro;
este paquete no decide permisos, no recibe proformas ni persiste correcciones.

Los archivos de prototipo `backend/` y `frontend/` se retiran de la ruta activa
en esta fase. Git conserva su historia y los informes de auditoría siguen siendo
evidencia; la SQLite nunca se convierte en datos comerciales.

Operación: ejecutar `make check`, `uv build` y la prueba de instalación antes
de publicar un artefacto. Publicar requiere definir el registro privado, la
versión de paquete y el manifiesto de despliegue del futuro backend; F06 no
despliega ni afirma que exista integración Django.
