"""Escucha y doble revisión local: no introducir textos privados en argumentos shell."""

import argparse
import getpass
import sys
from pathlib import Path

from training.benchmark_campo.pipeline import canonical

from . import human


def display_private(value):
    # Bypass stdout/stderr: private literals must never reach redirected logs.
    with open("/dev/tty", "w") as terminal:
        terminal.write(canonical(value))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "operation",
        choices=[
            "demo",
            "declare",
            "init",
            "status",
            "listen",
            "draft",
            "submit",
            "inspect",
            "adjudicate",
            "approve",
            "export",
            "vote",
            "score",
        ],
    )
    p.add_argument("--dataset", type=Path)
    p.add_argument("--project", type=Path)
    p.add_argument("--id", choices=human.IDS)
    p.add_argument("--reviewer")
    p.add_argument("--session")
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--end", type=float)
    p.add_argument("--run", type=Path)
    p.add_argument("--declarations", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--batch", type=Path)
    p.add_argument("--votes", type=Path)
    p.add_argument("--registry", type=Path)
    p.add_argument("--synthetic-test-data", action="store_true")
    a = p.parse_args(argv)
    try:
        if a.operation in {
            "draft",
            "submit",
            "inspect",
            "adjudicate",
            "approve",
            "vote",
            "declare",
        }:
            human.require(sys.stdin.isatty() and sys.stdout.isatty())
        if a.operation == "demo":
            human.create_demo(a.output)
        elif a.operation == "declare":
            human.require(sys.stdin.isatty() and sys.stdout.isatty())
            print(
                "Introduzca únicamente actas y permisos que un responsable ya haya proporcionado."
            )
            declared = {
                "batch_id": input("Alias de lote (A-Z/0-9/_/-): "),
                "frozen_date": input("Fecha del lote YYYY-MM-DD: "),
                "act_id": input("ID de acta de revisión: "),
                "reviewer_ids": input("Aliases de revisores separados por espacio: ").split(),
                "partition": "PREVIOUSLY_OPEN",
                "audio_retention_authorized": input("¿Acta permite conservar audio? SI/NO: ")
                == "SI",
                "publication_permission": {
                    "metrics": input("¿Permiso explícito de publicar métricas? SI/NO: ") == "SI",
                    "transcripts": input("¿Permiso explícito de publicar textos? SI/NO: ") == "SI",
                },
                "sessions": [],
            }
            if a.synthetic_test_data:
                declared["origin"] = "SYNTHETIC_TEST_ONLY"
            for case in human.IDS:
                print("Declaración para ID", case)
                declared["sessions"].append(
                    {
                        "id": case,
                        "speaker_id": input("Alias del hablante: "),
                        "consent": {
                            "human_declared": input("¿Consentimiento declarado? SI/NO: ") == "SI",
                            "act_id": input("ID de acta de consentimiento: "),
                            "use_policy_id": input("ID de política de uso: "),
                            "retention_policy_id": input("ID de política de retención: "),
                        },
                    }
                )
            human.require(
                input("Confirma que las declaraciones proceden de actas: CONFIRMO: ") == "CONFIRMO"
            )
            human.write_private(a.output, declared)
        elif a.operation == "init":
            human.initialize(a.dataset, a.project, synthetic=a.synthetic_test_data)
        elif a.operation == "status":
            print(canonical(human.status(a.dataset, a.project)), end="")
        elif a.operation == "listen":
            human.listen(a.dataset, a.project, a.id, a.start, a.end)
        elif a.operation in {"draft", "submit", "adjudicate", "approve"}:
            text = ""
            note = ""
            if a.operation != "approve":
                print("Escriba sólo lo oído. Texto oculto; nunca copiar ASR/guion.")
                text = getpass.getpass("Texto literal (una línea, sin precarga): ")
            if a.operation in {"adjudicate", "approve"}:
                note = getpass.getpass("Acta/razón; si resolvió dudas incluya RESUELTO: ")
            uncertain = False
            if a.operation in {"draft", "submit", "adjudicate"}:
                uncertain = input("¿Hay voz/palabras aún dudosas? [si/NO]: ") != "NO"
                if uncertain:
                    note += " " + getpass.getpass("Palabras/intervalos dudosos y motivo: ")
            explicit = input("Confirmo escucha humana propia, sin ASR/guion; escribir CONFIRMO: ")
            human.require(explicit == "CONFIRMO")
            action = {
                "draft": "DRAFT",
                "submit": "SUBMITTED",
                "adjudicate": "ADJUDICATED",
                "approve": "APPROVED",
            }[a.operation]
            human.append(
                a.dataset,
                a.project,
                a.id,
                action,
                a.reviewer,
                a.session,
                text=text,
                note=note,
                explicit=True,
                uncertain=uncertain,
                origin="SYNTHETIC_TEST_ONLY" if a.synthetic_test_data else "heard_audio",
            )
        elif a.operation == "inspect":
            _, _, states, _ = human.load_project(a.dataset, a.project)
            state = states[a.id]
            own = state["reads"].get(a.session)
            human.require(
                (own and own["reviewer"] == a.reviewer)
                or len(state["reads"]) == 2
                and all(r["action"] == "SUBMITTED" for r in state["reads"].values())
            )
            own = state["reads"].get(a.session)
            if own and own["reviewer"] == a.reviewer:
                display_private(own)
            else:
                display_private(state)
        elif a.operation == "export":
            human.export_reviewed(
                a.dataset,
                a.project,
                a.run,
                a.declarations,
                a.output,
                synthetic=a.synthetic_test_data,
            )
        elif a.operation == "vote":
            from training.benchmark_campo.pipeline import load

            batch = load(a.batch)
            for s in batch.sessions:
                display_private(
                    {
                        "session_id": s.session_id,
                        "reference": s.reference.model_dump(mode="json") if s.reference else None,
                        "consent": s.consent.model_dump(mode="json"),
                    }
                )
            print("Revisar TODOS los textos y permisos anteriores contra audio y actas externas.")
            decision = input("Decisión para todos: ACCEPT / REJECT / DISPUTE: ")
            attestation = input("ID de acta externa: ")
            note = getpass.getpass("Razón de la decisión: ")
            human.require(input("Escribir CONFIRMO para guardar: ") == "CONFIRMO")
            human.external_vote(
                a.batch, a.votes, a.registry, a.reviewer, attestation, decision, note
            )
        else:
            human.score_reviewed(a.batch, a.votes, a.registry, a.output)
        print(canonical({"ok": True, "operation": a.operation, "private_outputs": True}).strip())
        return 0
    except Exception:
        print(
            canonical(
                {
                    "ok": False,
                    "status": "BLOCKED_EXTERNAL",
                    "error": "PRIVATE_INPUT_OR_PROTOCOL_INCOMPLETE",
                }
            ).strip()
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
