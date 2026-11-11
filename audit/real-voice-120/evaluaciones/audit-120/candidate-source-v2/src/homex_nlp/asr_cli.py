"""CLI de audio: consume un temporal local y jamás lo conserva."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from homex_nlp.asr.faster_whisper_adapter import FasterWhisperAdapter
from homex_nlp.asr.service import AsrService
from homex_nlp.errors import HomexError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="homex-asr")
    parser.add_argument("audio", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--compute-type", default="int8")
    arguments = parser.parse_args(argv)
    try:
        adapter = FasterWhisperAdapter(
            arguments.model, device=arguments.device, compute_type=arguments.compute_type
        )
        result = AsrService(adapter).transcribe(arguments.audio)
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":")))
        return 0
    except HomexError as error:
        print(json.dumps(error.detail.model_dump(mode="json"), ensure_ascii=False), file=sys.stderr)
        return 2
    finally:
        arguments.audio.unlink(missing_ok=True)
