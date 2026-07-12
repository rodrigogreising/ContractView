"""Application-owned password verification contract."""

from typing import Protocol


class PasswordVerifierPort(Protocol):
    def matches(self, encoded_hash: str, candidate: str) -> bool: ...
