"""Invoice renderer provider configured by the integration composition root."""

from typing import Any, Callable

from .ports.package_rendering import InvoicePdfRendererPort

_factory: Callable[[], InvoicePdfRendererPort] | None = None


def configure_invoice_pdf_renderer_factory(
    factory: Callable[[], InvoicePdfRendererPort],
) -> None:
    global _factory
    _factory = factory


def render_invoice_pdf(invoice: dict[str, Any]) -> bytes:
    if _factory is None:
        raise RuntimeError("ContractView composition root has not configured package rendering")
    return _factory().render(invoice)
