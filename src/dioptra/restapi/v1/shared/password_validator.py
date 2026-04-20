# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
"""Password complexity validation for user accounts.

This module implements password complexity checks that align with NIST SP 800-63B
guidance. Rules are configurable via environment variables so that deployments with
stricter (FISMA/FedRAMP) requirements can tighten them without code changes.
"""

from __future__ import annotations

import os
import string
from pathlib import Path
from typing import Final, Iterable

# Default list of common/weak passwords that should never be accepted. Deployments
# can override or extend this list by pointing ``DIOPTRA_PASSWORD_BLOCKLIST_PATH``
# at a file containing one password per line.
_DEFAULT_BLOCKLIST: Final[frozenset[str]] = frozenset(
    {
        "password",
        "password1",
        "password123",
        "passw0rd",
        "p@ssw0rd",
        "qwerty",
        "qwerty123",
        "qwertyuiop",
        "letmein",
        "welcome",
        "welcome1",
        "admin",
        "administrator",
        "root",
        "changeme",
        "iloveyou",
        "monkey",
        "dragon",
        "abc123",
        "123456",
        "12345678",
        "123456789",
        "1234567890",
        "000000",
        "111111",
        "dioptra",
        "supersecurepassword",
    }
)

_SPECIAL_CHARACTERS: Final[frozenset[str]] = frozenset(string.punctuation)


class PasswordComplexityError(ValueError):
    """Raised when a password fails one or more complexity requirements."""

    def __init__(self, reasons: list[str]) -> None:
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


class PasswordValidator:
    """Validate passwords against a configurable set of complexity rules.

    The following rules are enforced:

    * Minimum length (default 15, configurable via ``DIOPTRA_PASSWORD_MIN_LENGTH``).
    * At least one uppercase letter, one lowercase letter, one digit, and one
      special character.
    * The password must not equal, or be trivially derived from, the username or
      email address associated with the account.
    * The password must not appear in the configured common-passwords blocklist.
    """

    DEFAULT_MIN_LENGTH: Final[int] = 15

    def __init__(
        self,
        min_length: int | None = None,
        blocklist: Iterable[str] | None = None,
    ) -> None:
        if min_length is None:
            min_length = self._min_length_from_env()
        if min_length < 1:
            raise ValueError("min_length must be a positive integer")
        self._min_length = min_length

        if blocklist is None:
            blocklist = self._blocklist_from_env()
        self._blocklist = frozenset(
            entry.strip().lower() for entry in blocklist if entry.strip()
        )

    @property
    def min_length(self) -> int:
        return self._min_length

    @property
    def blocklist(self) -> frozenset[str]:
        return self._blocklist

    def validate(
        self,
        password: str,
        username: str | None = None,
        email_address: str | None = None,
    ) -> None:
        """Validate ``password``, raising :class:`PasswordComplexityError` on failure.

        Args:
            password: The candidate password.
            username: The account's username, if available. Used to reject passwords
                that trivially match the username.
            email_address: The account's email address, if available. Used to reject
                passwords that trivially match the email or its local part.

        Raises:
            PasswordComplexityError: If any complexity rule is violated. The error
                aggregates every failing rule so the caller can surface all of them
                to the user at once.
        """
        if not isinstance(password, str):
            raise PasswordComplexityError(["Password must be a string."])

        reasons: list[str] = []
        reasons.extend(self._check_length(password))
        reasons.extend(self._check_character_classes(password))
        reasons.extend(self._check_identity_overlap(password, username, email_address))
        reasons.extend(self._check_blocklist(password))

        if reasons:
            raise PasswordComplexityError(reasons)

    def _check_length(self, password: str) -> list[str]:
        if len(password) < self._min_length:
            return [f"Password must be at least {self._min_length} characters long."]
        return []

    def _check_character_classes(self, password: str) -> list[str]:
        reasons: list[str] = []
        if not any(ch.isupper() for ch in password):
            reasons.append("Password must contain at least one uppercase letter.")
        if not any(ch.islower() for ch in password):
            reasons.append("Password must contain at least one lowercase letter.")
        if not any(ch.isdigit() for ch in password):
            reasons.append("Password must contain at least one digit.")
        if not any(ch in _SPECIAL_CHARACTERS for ch in password):
            reasons.append(
                "Password must contain at least one special character "
                f"(e.g. one of: {string.punctuation})."
            )
        return reasons

    @staticmethod
    def _check_identity_overlap(
        password: str,
        username: str | None,
        email_address: str | None,
    ) -> list[str]:
        reasons: list[str] = []
        lower_password = password.lower()

        if username and username.strip():
            if lower_password == username.strip().lower():
                reasons.append("Password must not match the username.")

        if email_address and email_address.strip():
            email_lower = email_address.strip().lower()
            if lower_password == email_lower:
                reasons.append("Password must not match the email address.")
            else:
                local_part = email_lower.split("@", 1)[0]
                if local_part and lower_password == local_part:
                    reasons.append(
                        "Password must not match the local part of the email address."
                    )
        return reasons

    def _check_blocklist(self, password: str) -> list[str]:
        if password.lower() in self._blocklist:
            return ["Password is too common and has been blocked."]
        return []

    @classmethod
    def _min_length_from_env(cls) -> int:
        raw = os.getenv("DIOPTRA_PASSWORD_MIN_LENGTH")
        if raw is None or not raw.strip():
            return cls.DEFAULT_MIN_LENGTH
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(
                f"Invalid DIOPTRA_PASSWORD_MIN_LENGTH value: {raw!r}. "
                "Expected a positive integer."
            ) from exc
        if value < 1:
            raise ValueError(
                f"Invalid DIOPTRA_PASSWORD_MIN_LENGTH value: {value}. "
                "Must be a positive integer."
            )
        return value

    @classmethod
    def _blocklist_from_env(cls) -> frozenset[str]:
        blocklist = set(_DEFAULT_BLOCKLIST)
        path = os.getenv("DIOPTRA_PASSWORD_BLOCKLIST_PATH")
        if path:
            blocklist_path = Path(path)
            if blocklist_path.is_file():
                with blocklist_path.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        entry = line.strip()
                        if entry and not entry.startswith("#"):
                            blocklist.add(entry.lower())
        return frozenset(blocklist)
