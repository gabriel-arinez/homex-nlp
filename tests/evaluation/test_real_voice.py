from tools.evaluate_real_voice import edit_counts, normalized_words


def test_edit_counts_preserve_all_observable_operations():
    result = edit_counts(["a", "b", "c"], ["a", "x", "c", "d"])
    assert result["substitutions"] == 1
    assert result["insertions"] == 1
    assert result["deletions"] == 0
    assert result["errors"] == 2
    assert result["reference_length"] == 3
    assert result["rate"] == 2 / 3


def test_normalization_does_not_hide_commercial_number_errors():
    assert normalized_words("¡Mesa, AZUL!") == ["mesa", "azul"]
    assert normalized_words("1,25 metros") != normalized_words("125 metros")
    assert normalized_words("NF-810") != normalized_words("NF-811")


def test_empty_reference_has_no_defined_rate():
    result = edit_counts([], ["noise"])
    assert result["insertions"] == 1
    assert result["rate"] is None
