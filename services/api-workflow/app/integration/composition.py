"""ContractView modular-monolith composition root."""

from __future__ import annotations

from contextlib import contextmanager

from ..application.transaction import configure_transaction_factory
from ..application.object_storage import configure_object_store_factory
from ..application.runtime_health import configure_runtime_health_factory
from ..application.extraction_provider import configure_extraction_adapter_factory
from ..application.ledger_documents import configure_spreadsheet_parser_factory
from ..application.package_rendering import configure_invoice_pdf_renderer_factory
from ..application.passwords import configure_password_verifier_factory

_composed = False


def compose() -> None:
    global _composed
    if _composed:
        return

    @contextmanager
    def factory():
        from ..adapters.persistence.postgres import postgres_transaction
        from ..settings import get_settings

        with postgres_transaction(get_settings().database_url) as transaction:
            yield transaction

    configure_transaction_factory(factory)

    def object_store_factory():
        from ..adapters.object_storage.minio import MinioArtifactObjectStore
        from ..runtime import object_store
        from ..settings import get_settings

        return MinioArtifactObjectStore(object_store(), get_settings().minio_bucket)

    configure_object_store_factory(object_store_factory)

    def runtime_health_factory():
        from .runtime_health import IntegratedRuntimeHealth

        return IntegratedRuntimeHealth()

    configure_runtime_health_factory(runtime_health_factory)

    def extraction_adapter_factory():
        from ..adapters.extraction.tesseract import TesseractCliAdapter

        return TesseractCliAdapter()

    configure_extraction_adapter_factory(extraction_adapter_factory)

    def password_verifier_factory():
        from ..adapters.identity.argon2 import Argon2PasswordVerifier

        return Argon2PasswordVerifier()

    configure_password_verifier_factory(password_verifier_factory)

    def spreadsheet_parser_factory():
        from ..adapters.ledger.openpyxl import OpenpyxlSpreadsheetParser

        return OpenpyxlSpreadsheetParser()

    configure_spreadsheet_parser_factory(spreadsheet_parser_factory)

    def invoice_pdf_renderer_factory():
        from ..adapters.packages.reportlab import ReportLabInvoicePdfRenderer

        return ReportLabInvoicePdfRenderer()

    configure_invoice_pdf_renderer_factory(invoice_pdf_renderer_factory)
    _composed = True
