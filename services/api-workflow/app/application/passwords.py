"""Password verifier provider configured by the integration composition root."""

from typing import Callable

from .ports.passwords import PasswordVerifierPort

_factory: Callable[[], PasswordVerifierPort] | None = None


def configure_password_verifier_factory(
    factory: Callable[[], PasswordVerifierPort],
) -> None:
    global _factory
    _factory = factory


def password_matches(encoded_hash: str, candidate: str) -> bool:
    if _factory is None:
        raise RuntimeError("ContractView composition root has not configured password verification")
    return _factory().matches(encoded_hash, candidate)
