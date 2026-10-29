"""Conflict veto recovered from PR24, adapted to V15 offline only."""

from copy import deepcopy


def reconcile(a, b, model_version):
    """A supplies structure. B can veto conflicting fields, never invent missing ones.

    Reuses the existing NER assembler as B; deliberately does not reuse its hybrid
    which can inherit NER quantity/price when rules abstain. No relation-by-position.
    """
    out = deepcopy(a)
    conflicts = []
    item, other = out["item_proposal"], b["item_proposal"]
    if item and other:
        if (item["name"] or "").casefold() != (other["name"] or "").casefold():
            conflicts.append("PRODUCT_DISAGREEMENT")
            out.update(item_proposal=None, status="NO_PROPOSAL", proposed_item_count=0)
            out["warnings"].append(
                {
                    "code": "NO_PRODUCT",
                    "path": "",
                    "severity": "REVIEW",
                    "message": "Offline engines disagree on the product; no proposal.",
                }
            )
            for c in out["candidates"]:
                c["component_ref"] = None
        else:
            quantity_conflict = (
                item["quantity"] is not None
                and other["quantity"] is not None
                and item["quantity"] != other["quantity"]
            )
            currency_conflict = any(
                w["code"] == "UNSUPPORTED_CURRENCY" for r in (a, b) for w in r["warnings"]
            )
            price_conflict = (
                item["price"] is not None
                and other["price"] is not None
                and any(
                    item["price"].get(k) != other["price"].get(k)
                    for k in ("mode", "currency", "stated_amount")
                )
            )
            labels = set()
            if quantity_conflict:
                conflicts.append("QUANTITY_DISAGREEMENT")
                item["quantity"] = None
                labels.add("CANTIDAD")
                out["warnings"].append(
                    {
                        "code": "NO_QUANTITY",
                        "path": "/item_proposal/quantity",
                        "severity": "REVIEW",
                        "message": "Offline quantity conflict; abstain.",
                    }
                )
            if quantity_conflict or currency_conflict or price_conflict:
                item["price"] = None  # Also invalidates any derived total/reference.
                labels.update({"PRECIO", "PRECIO_TOTAL", "PRECIO_UNITARIO"})
            if currency_conflict:
                conflicts.append("CURRENCY_CONFLICT")
            if price_conflict:
                conflicts.append("PRICE_DISAGREEMENT")
            for c in out["candidates"]:
                if c["label"] in labels:
                    c["decision"] = "UNRESOLVED"
                    if c["candidate_id"] not in item["unresolved"]:
                        item["unresolved"].append(c["candidate_id"])
    elif item and any(w["code"] == "UNSUPPORTED_CURRENCY" for w in b["warnings"]):
        item["price"] = None
        conflicts.append("CURRENCY_CONFLICT")
    if conflicts:
        out["warnings"].append(
            {
                "code": "CONFLICTING_VALUES",
                "path": "",
                "severity": "REVIEW",
                "message": "Offline NER/rules conflict; no field inferred.",
            }
        )
    used = {c["candidate_id"] for c in out["candidates"]}
    for i, c in enumerate(b["candidates"]):
        c = deepcopy(c)
        identifier = "offline-ner-" + str(i)
        while identifier in used:
            identifier += "-x"
        used.add(identifier)
        c.update(
            candidate_id=identifier,
            component_ref=None,
            decision="REJECTED",
            reason="Auxiliary NER audit; never a naive union of accepted fields.",
        )
        out["candidates"].append(c)
    out["engine"] = {
        "mode": "HYBRID",
        "rules_version": "offline-v15-ner-veto-v2",
        "normalization_version": "1.0",
        "model_version": model_version,
    }
    return out, conflicts


def evidence(result, labels, raw=False):
    spans = set()
    unmapped = set()
    for c in result["candidates"]:
        if not raw and c["decision"] != "ACCEPTED":
            continue
        label = c["label"]
        if (
            label == "PRECIO"
            and result.get("item_proposal")
            and result["item_proposal"].get("price")
        ):
            label = (
                "PRECIO_UNITARIO"
                if result["item_proposal"]["price"]["mode"] == "PRECIO_UNITARIO"
                else "PRECIO_TOTAL"
            )
        if label not in labels:
            unmapped.add(label)
            continue
        spans.add((c["start"], c["end"], label))
    return sorted(spans), sorted(unmapped)
