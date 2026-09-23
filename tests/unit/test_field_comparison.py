from homex_nlp.field_comparison import compare_fields


def test_field_comparison_is_pure_and_handles_empty_denominator() -> None:
    result = compare_fields(
        {"quantity": 2, "name": "escritorio"}, {"quantity": 3, "color": "nogal"}
    )
    assert result.corrected_fields == 1
    assert result.removed_fields == 1
    assert result.added_fields == 1
    assert result.field_precision == "0"
    empty = compare_fields({}, {})
    assert empty.field_precision is None and empty.item_equal is True
