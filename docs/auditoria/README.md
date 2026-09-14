# Evidencia de la auditoría

`resultados_sql.json` registra 16 comportamientos reproducidos en PostgreSQL 16.15. S01, S02 y S15 prueban protecciones existentes; los otros casos demuestran estados inconsistentes admitidos. Un resultado `verificado: true` indica reproducción, no aprobación del comportamiento.

Cada `S*.sql` crea datos de prueba con IDs 90001–90003, comprueba un comportamiento y termina en ROLLBACK. Ejecutar exclusivamente en una base de auditoría vacía donde se haya cargado `homex_bd.sql`, con `psql -v ON_ERROR_STOP=1 -f archivo.sql`. No apuntar estos casos a una base del negocio. El esquema original se carga una sola vez, también con `ON_ERROR_STOP`.

Durante esta revisión se ejecutó PostgreSQL en modo monousuario dentro de un directorio temporal, sin red. Para suministrar sentencias multilínea se usó `postgres --single -j`, eliminando líneas vacías del archivo de entrada y añadiendo un terminador de dos saltos de línea. No se alteró el contenido de las sentencias. Este modo no verifica concurrencia. Los casos son ejecutables mediante psql normal en una instancia de pruebas.

`verificar_python.py` utiliza el entorno virtual existente y la SQLite de la prueba se crea en un directorio temporal. Ejecutar desde la raíz:

```bash
backend/.venv/bin/python docs/auditoria/verificar_python.py
```

Genera `resultados_python.json`. Si cambian dataset, motor o dependencias, los resultados pueden cambiar; no son aserciones permanentes de comportamiento correcto. Las pruebas del conversor se hacen sobre su función, suministrando directamente el dataset real porque la ruta de su CLI es incorrecta.

Las salidas del motor corresponden a la ausencia del modelo HOMEX entrenado. No se invoca Whisper ni se importa `main.py`, para evitar carga ASR y escrituras de inicialización de la aplicación. Los resultados no son una evaluación F1 ni de audio.
