"""Application-owned deterministic package rendering contract."""

from typing import Any, Protocol


class InvoicePdfRendererPort(Protocol):
    def render(self, invoice: dict[str, Any]) -> bytes: ...
