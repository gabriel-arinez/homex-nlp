"""Process-level safety hook for validation subprocesses; no model training/loading."""

import importlib
import sys

FORBIDDEN = ("training.train_prf04", "spacy train", "spacy.cli.train --", "training/train_prf04.py")


def check_command(command):
    text = " ".join(str(c) for c in command) if isinstance(command, (list, tuple)) else str(command)
    if any(token in text for token in FORBIDDEN):
        raise RuntimeError("Training command prohibited in data-validation gate")


def install():
    def audit(event, args):
        if event == "subprocess.Popen":
            check_command(args[1])
        if event == "os.system":
            check_command(args[0])

    sys.addaudithook(audit)
    import spacy

    def denied(*args, **kwargs):
        raise RuntimeError("Training or model loading prohibited in corpus gate")

    importlib.import_module("spacy.cli.train").train = denied
    spacy.cli.train = denied
    spacy.load = denied
    spacy.language.Language.initialize = denied
    spacy.language.Language.update = denied
