"""Strict oral intake gate. Declarations require external human verification."""

import argparse
import json
import re
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Literal

import spacy
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, model_validator


class OralRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(pattern=r"^ORAL-[A-Z0-9-]+$")
    text: str = Field(min_length=1)
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    origin: Literal["SINTETICO_ORAL", "ASR_REAL", "TRANSCRIPCION_HUMANA"]
    split: Literal["train", "dev", "external_test", "quarantine"]
    source_case_id: str = Field(min_length=1)
    paraphrase_group_id: str = Field(min_length=1)
    template_id: str = Field(min_length=1)
    parent_record_id: str | None
    session_id: str | None
    speaker_id: str | None
    audio_sha256: str | None = Field(pattern=r"^[a-f0-9]{64}$")
    authorization_ref: str | None
    retention_policy_ref: str | None
    privacy_review_ref: str | None
    human_review_ref: str | None
    human_transcription_from_audio: StrictBool
    entities: list[tuple[StrictInt, StrictInt, str]]
    phenomena: list[
        Literal[
            "direct",
            "quantity",
            "capacity",
            "internal_quantity",
            "negation",
            "correction",
            "ellipsis",
            "missing",
            "noise",
            "price",
            "multiple_products",
        ]
    ]

    @model_validator(mode="after")
    def provenance(self):
        if self.text_sha256 != sha256(self.text.encode()).hexdigest():
            raise ValueError("TEXT_HASH")
        if self.origin == "SINTETICO_ORAL":
            if any(
                (
                    self.session_id,
                    self.speaker_id,
                    self.audio_sha256,
                    self.human_transcription_from_audio,
                )
            ):
                raise ValueError("SYNTHETIC_IS_NOT_AUDIO")
            if self.split == "external_test":
                raise ValueError("SYNTHETIC_IS_NOT_EXTERNAL_HUMAN_TEST")
        else:
            if not all(
                (
                    self.session_id,
                    self.speaker_id,
                    self.audio_sha256,
                    self.authorization_ref,
                    self.retention_policy_ref,
                    self.privacy_review_ref,
                )
            ):
                raise ValueError("REAL_PROVENANCE_REQUIRED")
            if self.origin == "TRANSCRIPCION_HUMANA" and not (
                self.human_transcription_from_audio and self.human_review_ref
            ):
                raise ValueError("HUMAN_REFERENCE_REQUIRED")
            if self.origin == "ASR_REAL" and self.human_transcription_from_audio:
                raise ValueError("ASR_IS_NOT_HUMAN_REFERENCE")
        if self.split == "external_test" and not self.human_review_ref:
            raise ValueError("EXTERNAL_REVIEW_REQUIRED")
        # Heuristic is additional to mandatory privacy review, never anonymization proof.
        if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b\d{7,}\b", self.text):
            raise ValueError("POTENTIAL_PERSONAL_DATA")
        return self


def validate(rows, labels, parent_splits):
    records = [OralRecord.model_validate(r) for r in rows]
    groups = {
        k: defaultdict(set)
        for k in (
            "source_case_id",
            "paraphrase_group_id",
            "template_id",
            "session_id",
            "speaker_id",
            "audio_sha256",
            "text_sha256",
        )
    }
    ids = set()
    tokenizer = spacy.blank("es")
    for row in records:
        if row.id in ids:
            raise ValueError("DUPLICATE_ID")
        ids.add(row.id)
        if row.parent_record_id:
            parent = parent_splits.get(row.parent_record_id)
            if parent is None or parent == "test" or parent != row.split:
                raise ValueError("PROTECTED_OR_UNKNOWN_PARENT")
        previous = 0
        doc = tokenizer.make_doc(row.text)
        for start, end, label in row.entities:
            if (
                label not in labels
                or not 0 <= start < end <= len(row.text)
                or start < previous
                or doc.char_span(start, end, alignment_mode="strict") is None
            ):
                raise ValueError("INVALID_ENTITY")
            previous = end
        for key, values in groups.items():
            value = getattr(row, key)
            if value:
                values[value].add(row.split)
    if any(len(splits) > 1 for values in groups.values() for splits in values.values()):
        raise ValueError("CROSS_SPLIT_GROUP")
    return {
        "format": "homex-oral-intake-1",
        "records": len(records),
        "synthetic": sum(r.origin == "SINTETICO_ORAL" for r in records),
        "real": sum(r.origin != "SINTETICO_ORAL" for r in records),
        "human_claims": sum(r.origin == "TRANSCRIPCION_HUMANA" for r in records),
        "external_authorizations_verified": False,
        "wer": None,
        "promotion": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    try:
        labels = set(json.loads((args.data / "manifests/prf04_labels.json").read_text())["labels"])
        parents = {}
        for path in (args.data / "splits").glob("*.json"):
            manifest = json.loads(path.read_text())
            for split, ids in manifest.get("assignments", {}).items():
                parents.update({identifier: split for identifier in ids})
        rows = [json.loads(line) for line in args.input.read_text().splitlines() if line.strip()]
        # JSON arrays become tuples only at the boundary, retaining strict integer validation.
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("RECORD_OBJECT_REQUIRED")
            if isinstance(row.get("entities"), list):
                row["entities"] = [tuple(e) if isinstance(e, list) else e for e in row["entities"]]
        print(json.dumps(validate(rows, labels, parents)))
    except (ValueError, TypeError, KeyError, OSError):
        print('{"status":"INVALID_ORAL_INPUT","details":"withheld_for_privacy"}')
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
