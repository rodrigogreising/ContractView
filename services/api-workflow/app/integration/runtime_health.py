"""Runtime health integration over PostgreSQL and MinIO adapters."""

from ..runtime import ensure_bucket, readiness


class IntegratedRuntimeHealth:
    def ensure_ready(self) -> None:
        ensure_bucket()

    def readiness(self) -> dict[str, bool]:
        return readiness()
