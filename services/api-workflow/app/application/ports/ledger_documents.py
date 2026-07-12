"""Application-owned spreadsheet parsing contract."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SpreadsheetRows:
    sheet: str
    rows: list[list[object]]


class SpreadsheetParserPort(Protocol):
    def parse_xlsx(self, content: bytes) -> SpreadsheetRows: ...
