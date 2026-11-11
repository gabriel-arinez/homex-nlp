# Reproduce final local integration evidence

Run: bash bootstrap.sh

Prerequisites: the three repositories at recorded local paths, backend .venv,
frontend installed node_modules, PostgreSQL 16 binaries, installed Playwright Chromium,
existing offline faster-whisper-small model, and unchanged voice corpus.
The NLP source must match ../source-hashes-before.json for this exact candidate.

Bootstrap creates a system temporary directory, copies pinned consumer sources and
installed frontend dependencies, generates a synthetic account/password, starts
its own UTF8 PostgreSQL clusters on unused loopback ports, and uses memory-broker
Celery eager execution with the real outbox publisher. No existing database or
ambient authenticated session is inspected. No dependency installation or external service.

The setup script contains complete generated-credential, fixture-copy and settings logic.
No generated password is stored in these delivered reproduction files. Reproduction
creates its own private config under the new scratch directory.

The backend runner executes the same 99 candidate-source consumer tests. The browser
probe performs one real WAV upload per category, checks response/form values,
and asserts no commercial writes or inventory changes before manual confirmation.
It does not save commercial records or test microphone capture. Browser context is fresh.

Runners stop their own processes through EXIT traps. Evidence goes beneath the new
scratch directory, never over delivered reports. Keep scratch until inspection finishes.
