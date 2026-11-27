"""Positive local material syntax, not number proximity, licenses bare gauges."""

import re


def contextual_gauge(text, start, end):
    before = text[max(0, start - 100) : start]
    after = text[end : end + 40]
    return bool(
        re.search(
            r"\b(?:melamina|MDF|MDP|HDF|tablero(?:\s+MDF)?|vidrio(?:\s+templado)?|tapacantos?|mes[oó]n\s+engrosado)\s+(?:de|a)\s+$",
            before,
            re.I,
        )
    ) and not re.match(
        r"\s*(?:de\s+)?(?:largo|longitud|ancho|alto|altura|fondo|profundidad|metros?|cm|bolivianos|d[oó]lares|unidades|piezas)\b",
        after,
        re.I,
    )
