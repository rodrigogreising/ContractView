"""Application-facing runtime health queries."""

from .ports.runtime_health import RuntimeHealthFactory

_factory: RuntimeHealthFactory | None = None


def configure_runtime_health_factory(factory: RuntimeHealthFactory) -> None:
    global _factory
    _factory = factory


def ensure_runtime_ready() -> None:
    if _factory is None:
        raise RuntimeError("ContractView composition root has not configured runtime health")
    _factory().ensure_ready()


def runtime_readiness() -> dict[str, bool]:
    if _factory is None:
        raise RuntimeError("ContractView composition root has not configured runtime health")
    return _factory().readiness()
