"""Argon2 password verification adapter."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class Argon2PasswordVerifier:
    def __init__(self) -> None:
        self._hasher = PasswordHasher()

    def matches(self, encoded_hash: str, candidate: str) -> bool:
        try:
            return self._hasher.verify(encoded_hash, candidate)
        except VerifyMismatchError:
            return False
