# NLP 0.1.25 controlled integration
Objective: publish the verified retake corrections, synchronize NLP/Backend main and verify existing Frontend compatibility. Baseline NLP6731115; candidate3d28b1b; Backend7842613; Frontendc0124c2.
Delivery: one cohesive NLP PR with explicit size exception, then Backend PR; no unrelated Frontend edits. Tests: package/pytest/contracts, 255 private NLP inputs, Backend real adapter/worker and cross-repo CI. No private audio upload.

## Specs
- S1: "Inspecciona el estado real y actualizado de los tres repositorios"; inspect local/remote branches, dependencies, versions, contracts, PRs and CI without touching unrelated work.
- S2: "Publica la rama correspondiente, crea el PR hacia `main` y comprueba las CI." Integrate commit `3d28b1bf043aef2fc00500a5f7f9b031352ff1bc` without rewriting it.
- S3: "Si corresponde publicar una nueva versión del paquete, utiliza versionado coherente con la versión estable actual `0.1.24`, sin sobrescribir artefactos publicados." New patch0.1.25, preserve old release manifests and artifacts.
- S4: "Actualiza la dependencia y su archivo de bloqueo." "Comprueba la integración real del adaptador NLP." "No modifiques reglas comerciales ni funcionalidades ajenas a la actualización del NLP."
- S5: "No realices modificaciones innecesarias en el Frontend." Verify current main contract/review/confirmation, preserve unrelated local changes.
- S6: "NLP → Backend → Frontend (solo si corresponde)." "Fusionar en `main` únicamente cuando las verificaciones estén aprobadas." "Confirmar que `main` contiene los cambios esperados y que la CI posterior a la fusión finaliza correctamente."
- S7: "No omitir ni desactivar controles para conseguir una CI verde." "No utilizar comandos Git destructivos ni modificar trabajos ajenos." "No publicar grabaciones privadas ni incorporar audios locales al repositorio."
- S8: "No aparecen regresiones en cantidades, precios, dimensiones o asociaciones de componentes." Verify120 historical and15 directed frozen captures using full outputs and ownership, not acoustic-certification claims.
- S9: "Los tres repositorios quedan actualizados y sincronizados con sus ramas remotas." "No quedan PR de esta intervención pendientes de integración." Report exact commits/PR/version/checks/main state; unrelated historical PRs remain untouched.

## Tasks
- T1 [S1-S3,S6-S8] inline, pending: patch release identity and immutable package, full isolated checks and independent verifier for risk item5; publish NLP branch/PR, wait all checks, merge, verify post-merge CI. Preserve3d28b1b. Source implementation already independently verified. One size exception approved; no chain rewriting.
- T2 [S4,S6-S9] inline, pending: fresh Backend worktree based on origin/main, wheel/pin/lock/strict adapter version/verifier references and focused consumer regression, independent dependency verification (risk item5), PR/CI/merge/post-merge CI.
- T3 [S5,S7,S9] read-only compatibility checks in clean Frontend main worktree if needed; no source changes unless proved necessary. Fast-forward local main refs without touching dirty working tree. Verify no new intervention PR remains open.

## Log
- L1 (2026-11-15): User requested integration/publication of NLP commit3d28b1b, updates to required consumers, approved CI before merge, no destructive commands/unrelated changes or private audio publication. Current remote main CI success: NLP43576682469, Backend43666875302, Frontend43577833614. NLP/Backend localmain equal remote; Frontend localmain behind16 commits and unrelated dirty feat/clientes-ux-20261115 checkout must be preserved.
- L2: User explicitly authorized current GitHub CLI session for gabriel-arinez/homex-nlp, homex-backend and only necessary Frontend changes. Final instruction verbatim: "si, procede, no hagas mas preguntas y deja todo actulizado, nlp y backend". Explicitly approved coherent oversized NLP PR preserving original commit. Treat remote release/branch/PR/merge/check operations as authorized only for this intervention.
- L3: Remote branch protections are absent on all3 mains; this does NOT waive any CI. Existing unrelated openPRs left untouched. GentleAI-specific issue-approval workflow is not present in HOMEX; follow actual HOMEX CI and preserve every native check. RDD remains globally disabled, not toggled.
- L4: T1 local verification passed:1080 tests; Ruff/format/schema/lock/reproducible/private installed-package checks;255 installed0.1.25 payloads exactly match corrected0.1.24 business results except request IDs/timing.15 audio hashes intact; ASR/contracts unchanged. Wheel d06c00a281dc5235655c5a830aaf5e7fba143dae002dbba0fe03a12a866d3933. Archived prior current manifest byte-exact. Parent26-test spotcheck passed. Independent verifier reports no blocker; remote CI remains pending before merge.
