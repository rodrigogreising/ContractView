"""Application-side immutable object-store provider."""

from .ports.object_storage import ArtifactObjectStoreFactory, ArtifactObjectStorePort

_factory: ArtifactObjectStoreFactory | None = None


def configure_object_store_factory(factory: ArtifactObjectStoreFactory) -> None:
    global _factory
    _factory = factory


def artifact_object_store() -> ArtifactObjectStorePort:
    if _factory is None:
        raise RuntimeError("ContractView composition root has not configured object storage")
    return _factory()
