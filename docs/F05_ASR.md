# F05 — ASR desacoplado y audio efímero

El paquete expone `AsrService`, que acepta un temporal privado validado, consume
todos los segmentos del adaptador y devuelve `TranscriptionResult`. El bloque
`finally` elimina el archivo tanto en éxito como en fallo, incluido un formato
inválido. No existen rutas de consulta, almacenamiento persistente ni backups
de audio en este repositorio.

`FasterWhisperAdapter` es perezoso: solo se importa al solicitar ASR y requiere
un directorio local de modelo. No descarga pesos ni cambia a un modelo alterno.
La dependencia vive en el extra `asr`.

Uso manual autorizado sobre un temporal local:

```bash
uv run --extra asr homex-asr /ruta/temporal.webm --model /ruta/modelo-local
```

El CLI borra la ruta indicada incluso si el modelo no está disponible. Aún no se
midió WER porque HOMEX no ha proporcionado sesiones de audio con referencia
humana; las pruebas usan dobles y bytes de prueba, no audios reales.
