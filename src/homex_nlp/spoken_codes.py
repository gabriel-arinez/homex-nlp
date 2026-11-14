"""Conservative explicit Spanish spelling grammar, never a product-code lookup."""

import re
import unicodedata

from homex_nlp.monetary import LEXICON, cardinal

_LETTERS = dict(
    zip(
        "a be ce de e efe ge hache i jota ka ele eme ene eñe o pe cu erre ese te u uve equis ye zeta".split(),
        "ABCDEFGHIJKLMNÑOPQRSTUVXYZ",
    )
)
_LETTERS.update({"ve": "V", "doble u": "W", "doble ve": "W", "doble uve": "W"})
_DIGITS = dict(zip("cero uno dos tres cuatro cinco seis siete ocho nueve".split(), "0123456789"))


def _fold(text):
    # Preserve ñ while removing pronunciation accents, including decomposed ones.
    return unicodedata.normalize(
        "NFC",
        "".join(
            c
            for c in unicodedata.normalize("NFD", text.lower())
            if unicodedata.category(c) != "Mn" or c == "\N{COMBINING TILDE}"
        ),
    )


def _is_spoken_start(raw):
    first = _fold(raw).split()[0] if raw.split() else ""
    return (
        first in _LETTERS
        or bool(re.fullmatch(r"[a-xzñ]", first))
        or first == "doble"
        or first in LEXICON
        or first.isdigit()
    )


def _spoken_code(raw):
    """Decode a complete phrase only: both a letter and a digit are mandatory."""
    words = _fold(raw).split()
    # At the start these are also ordinary model prepositions. An internal
    # letter after an unambiguous spelling token remains valid (be de...).
    if words and words[0] in {"de", "a"}:
        return None
    # A written initial needs another spelled letter before numeric decoding;
    # preserve abstention for mixed shorthand such as "B quince".
    if (
        words
        and words[0] not in _LETTERS
        and re.fullmatch(r"[a-xzñ]", words[0])
        and (len(words) < 2 or not re.fullmatch(r"[a-xzñ]", words[1]))
        and (len(words) < 2 or words[1] not in _LETTERS)
    ):
        return None
    output = []
    i = 0
    while i < len(words):
        word = words[i]
        pair = " ".join(words[i : i + 2])
        if pair in _LETTERS:
            output.append(_LETTERS[pair])
            i += 2
        elif word in _LETTERS or re.fullmatch(r"[a-xzñ]", word):
            # After a number, "o" may join alternative values, not spell O.
            if word == "o" and any(re.search(r"[0-9]", token) for token in output):
                return None
            output.append(_LETTERS.get(word, word.upper()))
            i += 1
        elif word in {"guion", "-"}:
            if not output or output[-1] == "-":
                return None
            output.append("-")
            i += 1
        else:
            end = i
            while end < len(words) and (
                words[end] in LEXICON or words[end] == "cero" or words[end].isdigit()
            ):
                end += 1
            chunk = words[i:end]
            if not chunk:
                return None
            if all(token in _DIGITS or re.fullmatch(r"[0-9]+", token) for token in chunk):
                number = "".join(_DIGITS.get(token, token) for token in chunk)
            else:
                value = cardinal(chunk)
                if value is None:
                    return None
                number = str(value)
            output.append(number)
            i = end
    code = "".join(output)
    if not re.fullmatch(r"[A-ZÑ0-9]+(?:-[A-ZÑ0-9]+)*", code):
        return None
    return code if re.search(r"[A-ZÑ]", code) and re.search(r"[0-9]", code) else None


def _spoken_code_status(raw):
    """Separate ordinary prepositions from incomplete explicit spelling."""
    words = _fold(raw).split()
    if not words or not _is_spoken_start(raw):
        return "NOT_CODE", None
    if words[0] in {"a", "de"} and (
        len(words) == 1 or (not _is_spoken_start(words[1]) and words[1] not in {"guion", "-"})
    ):
        return "NOT_CODE", None
    value = _spoken_code(raw)
    return ("CODE", value) if value is not None else ("AMBIGUOUS", None)
