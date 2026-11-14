# Reproduce three poltrona audio-to-browser checks

Run: bash bootstrap.sh

Requires the existing local repositories, backend .venv, frontend installed node_modules,
PostgreSQL 16 binaries, installed Playwright Chromium, offline faster-whisper-small model,
and the voice corpus at the paths recorded by candidate-identity.json and scripts.

The candidate must match ../source-hashes-before.json (24 modules), also matching
after-nlp-v5. The bootstrap copies pinned consumer commits to fresh system scratch,
copies installed frontend dependencies, creates private UTF8 PostgreSQL clusters
and synthetic login credentials, and starts only its own loopback API and preview.
No network install, production, ambient database, session or credentials are used.

The complete seed/fixture/settings generation is in live_setup_final.py.
Observed settings and a password-redacted config are preserved alongside it.
The memory-broker eager outbox worker calls the actual publisher and actual Whisper.
The browser uses real WAV copies for MP-0004, MP-0062 and MP-0067, requires OTRO routing,
and checks literal names, raw observations, price5500, no category-exclusive fields,
no commercial writes and unchanged inventory. It does not save a product or use a microphone.

bootstrap-observed.sh preserves the exact entry point used for the delivered run.
Do not execute that historical wrapper: it names the delivered evidence destination.
bootstrap.sh differs only by writing fresh evidence/logs under its new scratch directory.
Child runners stop their own services and clusters with EXIT traps; scratch remains
for inspection. The public bootstrap wrapper is structurally checked, not rerun.

Delivered audio-ledger-verification.json verifies all240 original AAC/WAV files.
The live browser probe itself uploads only the3 specified WAV copies, not120 recordings.
