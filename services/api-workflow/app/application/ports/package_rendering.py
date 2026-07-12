"""Application-owned deterministic package rendering contract."""

from typing import Any, Protocol

from ...shared_contracts import TemplateContract


class InvoicePdfRendererPort(Protocol):
    def render(self, invoice: dict[str, Any], template: TemplateContract) -> bytes: ...
