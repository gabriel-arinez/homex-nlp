"""Offline tokenizer for glued table punctuation; production tokenizer unchanged."""

import spacy
from spacy.util import compile_infix_regex, compile_suffix_regex


def create_nlp():
    nlp = spacy.blank("es")
    infixes = list(nlp.Defaults.infixes) + [
        r"[=:]",
        r"(?i:(?<=melamina)(?=puertas))",
        r"(?i:(?<=chapa)(?=de))",
        r"(?<=[A-Za-z])(?=\d)",
        r"(?<=\d)(?=[A-Za-z])",
        r"[()•]",
        r"(?<=[A-Za-z])\.(?=•)",
        r"(?<=[A-Za-z])\.(?=[A-Za-z])",
    ]
    nlp.tokenizer.suffix_search = compile_suffix_regex(
        list(nlp.Defaults.suffixes) + [r"(?<=º)\.", r"(?<=[A-Z])\."]
    ).search
    nlp.tokenizer.url_match = None
    nlp.tokenizer.infix_finditer = compile_infix_regex(infixes).finditer
    return nlp
