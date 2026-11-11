"""Excepciones públicas con detalle seguro; no incluir str(error) de terceros."""

from homex_nlp.contracts.error import ErrorDetail


class HomexError(Exception):
    def __init__(self, detail: ErrorDetail):
        self.detail = detail
        super().__init__(detail.message)
