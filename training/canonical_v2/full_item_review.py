"""Private full-item review scaffold; never treated as verified training gold.

The canonical NER corpus contains closed-scope excerpts. A full original item can
contain unannotated entities. This export preserves the *entire* item and maps all
known fragment spans back to it, without silently supervising unknown spans as O.
"""

from collections import defaultdict

from training.canonical_v2.io import digest


def full_item_review(items, excluded, excerpts):
    """Build private full-text review entries with byte-for-byte source anchors.

    The resulting entries are NOT supervised NER examples. Every item is kept,
    including quarantined originals and entries with zero recognized fragments.
    """
    item_ids = [item["id"] for item in items]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("FULL_ITEM_REVIEW_DUPLICATE_ITEM_ID")
    if not set(excluded) <= set(item_ids):
        raise ValueError("FULL_ITEM_REVIEW_UNKNOWN_QUARANTINE_ID")
    by_item = defaultdict(list)
    for row in excerpts:
        if row["origin"] != "DOCUMENTO_HOMEX_LITERAL":
            raise ValueError("FULL_ITEM_REVIEW_NON_DOCUMENTARY_FRAGMENT")
        links = [row["source_ref"], *row.get("additional_source_refs", [])]
        for link in links:
            by_item[link["source_item_id"]].append((row, link))

    if not set(by_item) <= set(item_ids):
        raise ValueError("FULL_ITEM_REVIEW_ORPHAN_FRAGMENT")

    result = []
    for item in items:
        text = item["item_text"]
        if item["char_end"] != item["char_start"] + len(text):
            raise ValueError("FULL_ITEM_REVIEW_SOURCE_BOUNDS_MISMATCH")
        fragments = []
        for row, link in by_item.get(item["id"], []):
            a, b = link["item_offset"]
            if not (0 <= a < b <= len(text)) or text[a:b] != row["text"]:
                raise ValueError("FULL_ITEM_REVIEW_ANCHOR_MISMATCH")
            if link["source_sha256"] != item["source_sha256"]:
                raise ValueError("FULL_ITEM_REVIEW_SOURCE_MISMATCH")
            if (
                link["char_start"] != item["char_start"] + a
                or link["char_end"] != item["char_start"] + b
            ):
                raise ValueError("FULL_ITEM_REVIEW_ABSOLUTE_OFFSET_MISMATCH")
            entities = []
            for start, end, label in row["entities"]:
                if not (0 <= start < end <= b - a):
                    raise ValueError("FULL_ITEM_REVIEW_ENTITY_BOUNDS")
                entities.append([a + start, a + end, label])
            fragments.append(
                {
                    "fragment_id": row["id"],
                    "start": a,
                    "end": b,
                    "text_sha256": row["text_sha256"],
                    "phenomena": row.get("phenomena", []),
                    "entities": entities,
                    "partial": True,
                }
            )
        fragments.sort(key=lambda x: (x["start"], x["end"], x["fragment_id"]))
        result.append(
            {
                "item_id": item["id"],
                "source_file": item["source_file"],
                "source_sha256": item["source_sha256"],
                "source_lines": [item["line_start"], item["line_end"]],
                "source_char_start": item["char_start"],
                "source_char_end": item["char_end"],
                "text": text,
                "text_sha256": digest(text),
                "fragments": fragments,
                "fragments_count": len(fragments),
                "review_state": "QUARANTINE"
                if item["id"] in excluded
                else "REQUIRES_FULL_ITEM_REVIEW",
                "annotation_scope": "INCOMPLETE_FULL_ITEM",
                "human_reviewed": False,
                "supervised": False,
                "eligible_for_training": False,
                "commercial_expected": None,
                "note": "Fragment spans are hints; complete entities, scopes and commercial relations must be adjudicated before supervision.",
            }
        )
    return result
