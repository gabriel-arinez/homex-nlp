"""Private opt-in offline audio evaluator; safe fixed-code stdout only."""

import argparse
from pathlib import Path

from training.benchmark_campo.pipeline import canonical, write_private

from .asr import Decode
from .dataset import PilotError
from .export import export_batch
from .runner import compare, evaluate, private_directory


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation", choices=["evaluate", "compare", "export"])
    p.add_argument("--dataset-dir", type=Path)
    p.add_argument("--output-dir", type=Path, required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--run-asr", action="store_true")
    p.add_argument("--model-dir", type=Path)
    p.add_argument("--expected-model-sha256")
    p.add_argument("--model-variant", choices=["base", "small"], default="base")
    p.add_argument("--language", choices=["es", "en"], default="es")
    p.add_argument("--beam-size", type=int, default=5)
    p.add_argument("--best-of", type=int, default=5)
    p.add_argument("--cpu-threads", type=int, default=2)
    p.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    p.add_argument("--compute-type", choices=["int8", "float32", "float16"], default="int8")
    p.add_argument("--vad-filter", action="store_true")
    p.add_argument("--no-condition-on-previous-text", action="store_true")
    p.add_argument("--run-dirs", nargs="+", type=Path)
    p.add_argument("--declarations", type=Path)
    p.add_argument("--annotations", type=Path)
    p.add_argument(
        "--synthetic-test-data",
        action="store_true",
        help="Explicit test marker; never evidence of real ASR accuracy",
    )
    a = p.parse_args(argv)
    try:
        if a.operation == "evaluate":
            if a.dataset_dir is None or (a.run_asr and a.model_dir is None):
                raise PilotError("DATASET_AND_EXPLICIT_LOCAL_MODEL_REQUIRED")
            result = evaluate(
                a.dataset_dir,
                a.output_dir,
                execute=a.run_asr,
                model_dir=a.model_dir,
                synthetic=a.synthetic_test_data,
                parameters=Decode(
                    language=a.language,
                    beam_size=a.beam_size,
                    best_of=a.best_of,
                    cpu_threads=a.cpu_threads,
                    device=a.device,
                    compute_type=a.compute_type,
                    variant=a.model_variant,
                    expected_model_sha256=a.expected_model_sha256,
                    vad_filter=a.vad_filter,
                    condition_on_previous_text=not a.no_condition_on_previous_text,
                ),
            )
        elif a.operation == "compare":
            result = compare(a.run_dirs or [])
            write_private(private_directory(a.output_dir) / "comparison.json", result)
        else:
            if not a.run_dirs or len(a.run_dirs) != 1 or a.declarations is None:
                raise PilotError("ONE_RUN_AND_EXTERNAL_DECLARATIONS_REQUIRED")
            result = export_batch(a.run_dirs[0], a.declarations, a.annotations)
            write_private(private_directory(a.output_dir) / "batch.json", result)
        print(canonical({"ok": True, "operation": a.operation, "private_outputs": True}).strip())
        return 2 if result.get("status") == "ASR_PARTIAL_FAILURE" else 0
    except Exception as exc:
        # Never emit Pydantic input_value, arbitrary model exceptions or real text.
        code = str(exc) if isinstance(exc, PilotError) else "INVALID_INPUT_OR_PRIVATE_OUTPUT"
        print(canonical({"ok": False, "error": code}).strip())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
