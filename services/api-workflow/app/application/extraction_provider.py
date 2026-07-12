"""Application-owned extraction-provider factory."""

from typing import Callable, Protocol


class ExtractionAdapterPort(Protocol):
    provider: str
    model: str

    def extract(self, filename: str, media_type: str, content: bytes): ...


_factory: Callable[[], ExtractionAdapterPort] | None = None


def configure_extraction_adapter_factory(factory: Callable[[], ExtractionAdapterPort]) -> None:
    global _factory
    _factory = factory


def extraction_adapter() -> ExtractionAdapterPort:
    if _factory is None:
        raise RuntimeError("ContractView composition root has not configured extraction")
    return _factory()
