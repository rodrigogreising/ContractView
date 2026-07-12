"""API composition entrypoint; HTTP behavior lives in app.http.api."""

from .integration.composition import compose

compose()

from .http.api import app  # noqa: E402

__all__ = ["app"]
