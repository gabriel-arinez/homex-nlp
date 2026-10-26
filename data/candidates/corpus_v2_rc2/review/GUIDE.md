# Revisión comercial humana real

Kit CSV/JSONL por campo: texto sintético, cita, before/after, alternativa, regla y prioridad.
Revisar P0 precios/cantidades primero, luego P1 unidades/ejes/relaciones y P2 descriptivos.
Completar decision=ACCEPT/REJECT/DISPUTE, reviewer, reviewed_at ISO-8601 con zona,
attestation_id de acta/autorización externa y comentario. No editar text_sha256, field_sha256 ni review_id. El hash del campo liga before/after y evita aceptar decisiones antiguas sobre referencias cambiadas.
Para modificaciones propuestas usar REJECT y proposed_value con evidencia en comentario;
el importador no reescribe dataset ni trata una propuesta como verdad adjudicada.

`python -m training.corpus_v2_rc2.review import <kit.jsonl> <decisions.jsonl> <output.json> --authorized-reviewers <registro_privado.json>`
Registro privado: lista de objetos reviewer/attestation_id/authorized=true; se suministra por responsable
autorizado, nunca por el generador. No es autenticación criptográfica y debe verificarse externamente.
Sin este registro no se importa nada. IDs o fechas escritos por un algoritmo no acreditan humanidad.
El importador solo produce un ledger separado, no activa corpus ni cambia V1.
Dos revisores reales autorizados independientes que acepten todos los campos sin contradicción
permiten GOLD_ELIGIBLE en el ledger; una aceptación permite HUMAN_REVIEWED por campo.
Rechazos/desacuerdos permanecen pendientes; un campo sin respuesta impide gold por registro.
Los estados no equivalen a homologación productiva. El kit inicial tiene cero respuestas.

Ítems privados: índice fuera de Git con archivo/hash/bloque/líneas y estado VERIFICABLE/DUDOSO/
INCONSISTENTE/REQUIERE_REVISION_HUMANA. Conservar cuatro referencias parciales en cuarentena.
Fuentes, precios negociados y opiniones privadas no se añaden al kit público.
