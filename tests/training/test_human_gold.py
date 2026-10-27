"""SYNTHETIC_TEST_ONLY: generated WAVs, simulated people; never human evidence."""

import json

import pytest

from tests.training.test_audio_pilot import dataset, stub_run  # noqa: F401, F811
from training.audio_pilot import human
from training.audio_pilot.dataset import PilotError
from training.benchmark_campo.metrics import alignment
from training.benchmark_campo.pipeline import digest, load, score, write_private


@pytest.fixture
def project(dataset, tmp_path):  # noqa: F811
    root, _ = dataset
    out = tmp_path / "private-ledger"
    human.initialize(root, out, synthetic=True)
    return root, out


def add(project, case="01", action="SUBMITTED", reviewer="R1", session="S1", text="uno dos", **kw):
    human.append(
        *project,
        case,
        action,
        reviewer,
        session,
        text=text,
        explicit=True,
        origin="SYNTHETIC_TEST_ONLY",
        **kw,
    )


def complete(project, case="01", second="uno tres"):
    add(project, case)
    add(project, case, reviewer="R2", session="S2", text=second)
    add(project, case, action="ADJUDICATED", note="Reescucha y acuerdo explícito")
    add(project, case, action="APPROVED", note="Aprobado personalmente")
    add(project, case, action="APPROVED", reviewer="R2", session="S2", note="Aprobado")


def test_resume_disagreement_adjudication_approval(project):
    add(project, action="DRAFT", text="uno")
    assert human.status(*project)["01"]["status"] == "DRAFT"
    add(project, action="DRAFT", text="uno dos")
    add(project)
    add(project, reviewer="R2", session="S2", text="uno tres")
    assert human.status(*project)["01"]["status"] == "DISAGREEMENT"
    add(project, action="ADJUDICATED", note="Reescucha")
    assert human.status(*project)["01"]["status"] == "ADJUDICATED"
    add(project, action="APPROVED", note="Sí")
    add(project, action="APPROVED", reviewer="R2", session="S2", note="Sí")
    assert human.status(*project)["01"]["status"] == "APPROVED"
    assert len(human.load_project(*project)[1]) == 7
    with pytest.raises(PilotError):
        add(project, action="DRAFT", text="modificación")


def test_identical_reads_never_automatically_approve(project):
    add(project)
    add(project, reviewer="R2", session="S2")
    assert human.status(*project)["01"]["status"] == "SUBMITTED"
    with pytest.raises(PilotError):
        add(project, action="APPROVED", note="Automático")


def test_single_person_two_sessions_stays_blocked(project):
    add(project)
    with pytest.raises(PilotError):
        add(project, action="APPROVED", note="Falsa doble")
    add(project, session="S2")
    add(project, action="ADJUDICATED", note="Dos sesiones de una persona")
    add(project, action="APPROVED", note="Primera")
    with pytest.raises(PilotError):
        add(project, action="APPROVED", session="S2", note="No es otro observador")
    assert human.status(*project)["01"]["status"] == "ADJUDICATED"


@pytest.mark.parametrize(
    "change",
    [
        {"origin": "asr"},
        {"origin": "script"},
        {"explicit": False},
        {"text": ""},
        {"session": "../X"},
        {"reviewer": "persona privada"},
    ],
)
def test_invalid_captures(project, change):
    args = (
        dict(text="uno", explicit=True, origin="SYNTHETIC_TEST_ONLY", session="S1", reviewer="R1")
        | change
    )
    with pytest.raises(ValueError):
        human.append(*project, "01", "SUBMITTED", **args)


def test_uncertain_requires_explicit_resolution(project):
    add(project, uncertain=True, note="Voz dudosa 0.01 s")
    add(project, reviewer="R2", session="S2")
    with pytest.raises(PilotError):
        add(project, action="ADJUDICATED", note="Suponer")
    add(project, action="ADJUDICATED", note="RESUELTO por reescucha segmentada")


@pytest.mark.parametrize(
    "mutation",
    [
        "hash",
        "session",
        "dataset",
        "extra",
        "orphan",
        "symlink",
        "permissions",
        "duplicate-json",
        "deleted",
    ],
)
def test_integrity_mutations(project, mutation):
    add(project)
    root, directory = project
    path = directory / "000001.json"
    event = json.loads(path.read_text())
    if mutation in {"hash", "dataset", "session", "extra"}:
        key, value = {
            "hash": ("audio_sha256", "f" * 64),
            "dataset": ("dataset_digest", "f" * 64),
            "session": ("id", "02"),
            "extra": ("auto_certified", True),
        }[mutation]
        event[key] = value
        path.write_text(json.dumps(event))
    elif mutation == "orphan":
        path.rename(directory / "000003.json")
    elif mutation == "deleted":
        add(project, reviewer="R2", session="S2")
        path.unlink()
    elif mutation == "permissions":
        path.chmod(0o644)
    elif mutation == "duplicate-json":
        path.write_text('{"id":"01",' + path.read_text()[1:])
    else:
        source = directory.parent / "outside.json"
        path.rename(source)
        path.symlink_to(source)
    with pytest.raises(ValueError):
        human.load_project(root, directory)


def test_wav_changed_and_cross_session_and_repeat(project):
    add(project)
    with pytest.raises(PilotError):
        add(project)  # cannot replace submitted evidence
    with pytest.raises(PilotError):
        add(project, reviewer="R2")  # session already owned by R1
    root, _ = project
    with (root / "audios/01.wav").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(PilotError):
        human.status(*project)


def test_no_gold_without_all_twenty_and_declarations(project, tmp_path):
    with pytest.raises(PilotError):
        human.export_reviewed(*project, tmp_path, tmp_path, tmp_path / "out")
    for case in human.IDS:
        complete(project, case)
    # A synthetic project cannot be relabeled into real HUMAN_GOLD by exporter.
    with pytest.raises(PilotError):
        human.export_reviewed(*project, tmp_path, tmp_path, tmp_path / "out")


def test_safe_status_cli_and_no_noninteractive_capture(project, capsys):
    from training.audio_pilot.human_cli import main

    root, out = project
    add(project, text="PRIVATE_SENTINEL")
    args = ["--dataset", str(root), "--project", str(out)]
    assert main(["status", *args]) == 0
    assert "PRIVATE_SENTINEL" not in capsys.readouterr().out
    assert main(["submit", *args, "--id", "01"]) == 2
    assert "BLOCKED_EXTERNAL" in capsys.readouterr().out


def real_shaped_project(project):
    """Simulated external declarations ONLY, generated audio never actual pilot evidence."""
    root, directory = project
    p = human.private_read(directory / "project.json")
    p["manifest"]["source_type"] = "PILOTO_REAL_DIAGNOSTICO_CONOCIDO"
    (directory / "project.json").write_text(json.dumps(p))
    return root, directory


@pytest.mark.parametrize("synthetic", [False, True])
def test_existing_export_and_scorer_end_to_end(dataset, tmp_path, monkeypatch, synthetic):  # noqa: F811
    # Use real transport shape to exercise external review gates with fake people;
    # all input WAVs and references remain SYNTHETIC_TEST_ONLY fixtures.
    monkeypatch.delenv("CI", raising=False)
    root, _ = dataset
    directory = tmp_path / "ledger"
    human.initialize(root, directory, synthetic=True)
    project = (root, directory) if synthetic else real_shaped_project((root, directory))
    for case in human.IDS:
        for reviewer, session in [("R1", "S1"), ("R2", "S2")]:
            human.append(
                *project,
                case,
                "SUBMITTED",
                reviewer,
                session,
                text="uno dos",
                explicit=True,
                origin="SYNTHETIC_TEST_ONLY" if synthetic else "heard_audio",
            )
        human.append(
            *project,
            case,
            "ADJUDICATED",
            "R1",
            "S1",
            text="uno dos",
            note="SYNTHETIC_TEST_ONLY",
            origin="SYNTHETIC_TEST_ONLY" if synthetic else "heard_audio",
            explicit=True,
        )
        for reviewer, session in [("R1", "S1"), ("R2", "S2")]:
            human.append(
                *project,
                case,
                "APPROVED",
                reviewer,
                session,
                note="SYNTHETIC_TEST_ONLY",
                origin="SYNTHETIC_TEST_ONLY" if synthetic else "heard_audio",
                explicit=True,
            )
    run_dir = stub_run(dataset, tmp_path)
    run = human.load_run(run_dir)
    if not synthetic:
        run["input"]["source_type"] = "PILOTO_REAL_DIAGNOSTICO_CONOCIDO"
    from training.audio_pilot.runner import quality

    run["quality_digest"] = digest(quality(run))
    (run_dir / "run.json").write_text(json.dumps(run))
    declaration = {
        "batch_id": "SYNTHETIC-TEST",
        "frozen_date": "2026-10-26",
        "partition": "PREVIOUSLY_OPEN",
        "audio_retention_authorized": True,
        "publication_permission": {"metrics": False, "transcripts": False},
        "act_id": "TEST-ACT",
        "reviewer_ids": ["R1", "R2"],
        "sessions": [
            {
                "id": case,
                "speaker_id": "TEST-SPEAKER",
                "consent": {
                    "human_declared": True,
                    "act_id": "TEST-ACT",
                    "use_policy_id": "TEST-USE",
                    "retention_policy_id": "TEST-RETENTION",
                },
            }
            for case in human.IDS
        ],
    }
    if synthetic:
        declaration["origin"] = "SYNTHETIC_TEST_ONLY"
    declarations = tmp_path / "declarations"
    declarations.mkdir(mode=0o700)
    source = declarations / "declarations.json"
    write_private(source, declaration)
    out = tmp_path / "export"
    # Missing/invalid permissions always block before generating a batch.
    for key in ["audio_retention_authorized", "publication_permission", "reviewer_ids", "act_id"]:
        bad = declaration.copy()
        bad.pop(key)
        source.write_text(json.dumps(bad))
        with pytest.raises(ValueError):
            human.export_reviewed(*project, run_dir, source, out, synthetic=synthetic)
    source.write_text(json.dumps(declaration))
    human.export_reviewed(*project, run_dir, source, out, synthetic=synthetic)
    batch = load(out / "batch.json")
    # No external votes => scorer excludes WER even with approved local ledger.
    assert synthetic or all(
        d["wer"]["status"] == "NOT_EVALUABLE"
        for d in score(batch, private_detail=True)["PRIVATE_DETAIL_DO_NOT_PUBLISH"]["per_session"]
    )
    registry = declarations / "registry.json"
    write_private(
        registry,
        [{"reviewer": r, "attestation_id": "TEST-ACT", "authorized": True} for r in ["R1", "R2"]],
    )
    votes = tmp_path / "votes"
    human.external_vote(out / "batch.json", votes, registry, "R1", "TEST-ACT", "ACCEPT", "test")
    with pytest.raises(PilotError):
        human.score_reviewed(out / "batch.json", votes, registry, declarations / "score.json")
    human.external_vote(out / "batch.json", votes, registry, "R2", "TEST-ACT", "ACCEPT", "test")
    result = human.score_reviewed(out / "batch.json", votes, registry, declarations / "score.json")
    assert result["HOLDOUT_EXTERNO"] == 0
    assert len(result["PRIVATE_DETAIL_DO_NOT_PUBLISH"]["per_session"]) == 20
    assert result["PRIVATE_DETAIL_DO_NOT_PUBLISH"]["per_session"][0]["wer"] == alignment(
        "uno dos", " TEXTO_SINTETICO_PRIVADO"
    )
    with pytest.raises(FileExistsError):
        human.external_vote(out / "batch.json", votes, registry, "R2", "TEST-ACT", "ACCEPT", "test")


def test_sdi_existing_scorer():
    assert alignment("a b c", "a x c")["S"] == 1
    assert alignment("a b c", "a c")["D"] == 1
    assert alignment("a c", "a b c")["I"] == 1
    assert alignment("", "ruido")["wer"] is None


def test_segmented_playback_no_audio_device(project, monkeypatch):
    calls = []
    monkeypatch.setattr(human.subprocess, "run", lambda *a, **kw: calls.append(a))
    # private_path also uses subprocess.run; preserve that dependency.
    from training.benchmark_campo import pipeline

    monkeypatch.setattr(pipeline, "private_path", lambda p: None)
    human.listen(*project, "01", 0.001, 0.003)
    assert calls[-1][0] == ["aplay", "-q"]
    with pytest.raises(PilotError):
        human.listen(*project, "01", -1, 1)


def test_guided_cli_capture_does_not_echo_literal(project, monkeypatch, capsys):
    from training.audio_pilot import human_cli

    monkeypatch.setattr(human_cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(human_cli.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(human_cli.getpass, "getpass", lambda _: "SYNTHETIC_PRIVATE_SENTINEL")
    answers = iter(["NO", "CONFIRMO"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    root, out = project
    assert (
        human_cli.main(
            [
                "submit",
                "--dataset",
                str(root),
                "--project",
                str(out),
                "--id",
                "01",
                "--reviewer",
                "R1",
                "--session",
                "S1",
                "--synthetic-test-data",
            ]
        )
        == 0
    )
    assert "SYNTHETIC_PRIVATE_SENTINEL" not in capsys.readouterr().out
    assert human.status(*project)["01"]["submitted"] == 1


def test_demo_is_audible_synthetic_and_not_gold(tmp_path):
    from training.audio_pilot.dataset import validate

    out = tmp_path / "demo"
    human.create_demo(out)
    manifest = validate(out / "dataset", synthetic=True)
    assert manifest["source_type"] == "SINTETICO_SOLO_PRUEBA"
    assert len({e["audio_sha256"] for e in manifest["entries"]}) == 20
    assert all(e["duration_seconds"] == 1 for e in manifest["entries"])
    assert human.status(out / "dataset", out / "project")["01"]["readings"] == 0
    run = human.load_run(out / "run")
    assert run["model"]["model_digest"] == "SYNTHETIC_TEST_ONLY"
    with pytest.raises(PilotError):
        human.export_reviewed(out / "dataset", out / "project", out / "run", out, out / "export")


def test_project_symlink_and_traversal_are_rejected(project):
    root, out = project
    alias = out.parent / "alias"
    alias.symlink_to(out, target_is_directory=True)
    with pytest.raises(PilotError):
        human.load_project(root, alias)
    with pytest.raises(PilotError):
        add(project, case="../01")


def test_private_writer_rejects_ancestor_symlink_and_traversal(tmp_path):
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(folder, target_is_directory=True)
    with pytest.raises(PilotError):
        human.write_private(link / "text.json", {"text": "SYNTHETIC_TEST_ONLY"})
    with pytest.raises(PilotError):
        human.write_private(folder / ".." / "text.json", {})
    assert not list(folder.iterdir())


def test_private_terminal_never_writes_stdout(monkeypatch, capsys):
    import io

    from training.audio_pilot.human_cli import display_private

    class Terminal(io.StringIO):
        def close(self):
            pass

    terminal = Terminal()
    monkeypatch.setattr("builtins.open", lambda path, mode: terminal)
    display_private({"text": "SYNTHETIC_PRIVATE_SENTINEL"})
    assert "SYNTHETIC_PRIVATE_SENTINEL" in terminal.getvalue()
    assert capsys.readouterr().out == ""
