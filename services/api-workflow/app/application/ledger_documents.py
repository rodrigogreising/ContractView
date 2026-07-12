"""Spreadsheet parser provider configured by the integration composition root."""

from typing import Callable

from .ports.ledger_documents import SpreadsheetParserPort, SpreadsheetRows

_factory: Callable[[], SpreadsheetParserPort] | None = None


def configure_spreadsheet_parser_factory(
    factory: Callable[[], SpreadsheetParserPort],
) -> None:
    global _factory
    _factory = factory


def parse_xlsx(content: bytes) -> SpreadsheetRows:
    if _factory is None:
        raise RuntimeError("ContractView composition root has not configured spreadsheet parsing")
    return _factory().parse_xlsx(content)
