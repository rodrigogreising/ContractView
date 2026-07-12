"""Application-owned runtime readiness port."""

from typing import Protocol


class RuntimeHealthPort(Protocol):
    def ensure_ready(self) -> None: ...
    def readiness(self) -> dict[str, bool]: ...


class RuntimeHealthFactory(Protocol):
    def __call__(self) -> RuntimeHealthPort: ...
