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
"""The server-side functions that perform auth endpoint operations."""

import datetime
import os
import uuid
from typing import Any, Final

import structlog
from flask_login import current_user, login_user, logout_user
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db.repository.utils import DeletionPolicy
from dioptra.restapi.db.unit_of_work import UnitOfWork
from dioptra.restapi.errors import (
    AccountLockedError,
    UserDoesNotExistError,
    UserPasswordError,
)
from dioptra.restapi.v1.users.service import UserPasswordService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

DEFAULT_MAX_LOGIN_ATTEMPTS: Final[int] = 5
DEFAULT_LOCKOUT_DURATION_MINUTES: Final[int] = 30


def _positive_int_from_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(
            f"Invalid {name} value: {raw!r}. Expected a positive integer."
        ) from exc
    if value < 1:
        raise ValueError(f"Invalid {name} value: {value}. Must be a positive integer.")
    return value


def _max_login_attempts() -> int:
    return _positive_int_from_env(
        "DIOPTRA_MAX_LOGIN_ATTEMPTS", DEFAULT_MAX_LOGIN_ATTEMPTS
    )


def _lockout_duration() -> datetime.timedelta:
    minutes = _positive_int_from_env(
        "DIOPTRA_LOCKOUT_DURATION_MINUTES", DEFAULT_LOCKOUT_DURATION_MINUTES
    )
    return datetime.timedelta(minutes=minutes)


class AuthService(object):
    """The service methods for user logins and logouts."""

    @inject
    def __init__(
        self, user_password_service: UserPasswordService, uow: UnitOfWork
    ) -> None:
        """Initialize the authentication service.

        All arguments are provided via dependency injection.

        Args:
            user_password_service: A UserPasswordService object.
        """
        self._user_password_service = user_password_service
        self._uow = uow

    def login(
        self,
        username: str,
        password: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Login the user with the given username and password.

        Args:
            username: The username for logging into the user account.
            password: The password for authenticating the user account.

        Returns:
            A dictionary containing the login success message.

        Raises:
            UserDoesNotExistError: If the user is not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        user = self._uow.user_repo.get_by_name(username, DeletionPolicy.NOT_DELETED)
        if not user:
            raise UserDoesNotExistError(username=username)

        now = datetime.datetime.now(tz=datetime.timezone.utc)

        if user.locked_until is not None and user.locked_until > now:
            log.debug(
                "Login rejected: account locked",
                user_id=user.user_id,
                locked_until=user.locked_until.isoformat(),
            )
            raise AccountLockedError(
                username=user.username, locked_until=user.locked_until
            )

        try:
            self._user_password_service.authenticate(
                password=password,
                user_password=str(user.password),
                expiration_date=user.password_expire_on,
                error_if_failed=True,
                log=log,
            )
        except UserPasswordError:
            self._register_failed_login(user=user, log=log)
            raise

        with self._uow:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login_on = datetime.datetime.now(tz=datetime.timezone.utc)

        login_user(user, remember=True)
        log.debug("Login successful", user_id=user.user_id)
        return {"status": "Login successful", "username": username}

    def _register_failed_login(self, user: Any, **kwargs) -> None:
        """Record a failed login attempt and lock the account if the threshold is hit."""
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        max_attempts = _max_login_attempts()
        lockout_duration = _lockout_duration()

        with self._uow:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= max_attempts:
                user.locked_until = (
                    datetime.datetime.now(tz=datetime.timezone.utc) + lockout_duration
                )
                log.debug(
                    "Account locked after repeated failed logins",
                    user_id=user.user_id,
                    failed_login_attempts=user.failed_login_attempts,
                    locked_until=user.locked_until.isoformat(),
                )

    def logout(self, everywhere: bool, **kwargs) -> dict[str, Any]:
        """Log the current user out.

        Args:
            everywhere: If True, log out from all devices by regenerating the current
                user's alternative id.

        Returns:
            A dictionary containing the logout success message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        user_id = current_user.user_id
        username = current_user.username

        if everywhere:
            with self._uow:
                current_user.alternative_id = uuid.uuid4()

        logout_user()
        log.debug("Logout successful", user_id=user_id, everywhere=everywhere)
        return {
            "status": "Logout successful",
            "username": username,
            "everywhere": everywhere,
        }
