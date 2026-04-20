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
"""Test suite for user operations.

This module contains a set of tests that validate the CRUD operations and additional
functionalities for the user entity. The tests ensure that the users can be registered,
modified, and deleted as expected through the REST API.
"""

from http import HTTPStatus
from typing import Any

from freezegun import freeze_time

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient

from ..lib import helpers
from ..test_utils import assert_retrieving_resource_works

# -- Assertions ----------------------------------------------------------------


def assert_user_response_contents_matches_expectations(
    response: dict[str, Any],
    expected_contents: dict[str, Any],
    current_user: bool = False,
) -> None:
    """Assert that user response contents is valid.

    Args:
        response: The actual response from the API.
        expected_contents: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response or if the response contents is not
            valid.
    """

    expected_keys = {
        "username",
        "email",
        "id",
    }
    if current_user:
        expected_keys.update(
            {
                "groups",
                "createdOn",
                "lastModifiedOn",
                "lastLoginOn",
                "passwordExpiresOn",
            }
        )
    assert set(response.keys()) == expected_keys

    # Validate non-Ref fields
    assert isinstance(response["username"], str)
    assert isinstance(response["email"], str)
    assert isinstance(response["id"], int)

    assert response["username"] == expected_contents["username"]
    assert response["email"] == expected_contents["email"]

    if current_user:
        assert isinstance(response["createdOn"], str)
        assert isinstance(response["lastModifiedOn"], str)
        assert isinstance(response["lastLoginOn"], (str, type(None)))
        assert isinstance(response["passwordExpiresOn"], str)

        assert helpers.is_iso_format(response["createdOn"])
        assert helpers.is_iso_format(response["lastModifiedOn"])
        if response["lastLoginOn"] is not None:
            assert helpers.is_iso_format(response["lastLoginOn"])
        assert helpers.is_iso_format(response["passwordExpiresOn"])

        # Validate the GroupRef structure
        assert isinstance(response["groups"][0]["id"], int)
        assert isinstance(response["groups"][0]["name"], str)
        assert isinstance(response["groups"][0]["url"], str)


def assert_retrieving_user_by_id_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    user_id: int,
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving a user by id works.

    Args:
        dioptra_client: The Dioptra client.
        user_id: The id of the user to retrieve.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.users.get_by_id(user_id)
    assert response.status_code == HTTPStatus.OK and response.json() == expected


def assert_retrieving_current_user_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: dict[str, Any],
) -> None:
    """Assert that retrieving the current user works.

    Args:
        dioptra_client: The Dioptra client.
        expected: The expected response from the API.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    response = dioptra_client.users.get_current()
    to_ignore = ["lastLoginOn", "lastModifiedOn"]
    response_info_filtered = {
        k: v for k, v in response.json().items() if k not in to_ignore
    }
    expected_filtered = {k: v for k, v in expected.items() if k not in to_ignore}
    assert (
        response.status_code == HTTPStatus.OK
        and response_info_filtered == expected_filtered
    )


def assert_retrieving_users_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    expected: list[dict[str, Any]],
    search: str | None = None,
    paging_info: dict[str, int] | None = None,
) -> None:
    """Assert that retrieving all users works.

    Args:
        dioptra_client: The Dioptra client.
        expected: The expected response from the API.
        search: The search string used in query parameters.
        paging_info: The paging information used in query parameters.

    Raises:
        AssertionError: If the response status code is not 200 or if the API response
            does not match the expected response.
    """
    assert_retrieving_resource_works(
        dioptra_client=dioptra_client.users,
        expected=expected,
        search=search,
        paging_info=paging_info,
    )


def assert_registering_existing_username_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    existing_username: str,
    non_existing_email: str,
) -> None:
    """Assert that registering a user with an existing username fails.

    Args:
        dioptra_client: The Dioptra client.
        username: The username to assign to the new user.

    Raises:
        AssertionError: If the response status code is not 409.
    """
    password = "SuperSecure!Pwd123"
    response = dioptra_client.users.create(
        username=existing_username, email=non_existing_email, password=password
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_registering_existing_email_fails(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    non_existing_username: str,
    existing_email: str,
) -> None:
    """Assert that registering a user with an existing username fails.

    Args:
        dioptra_client: The Dioptra client.
        username: The username to assign to the new user.

    Raises:
        AssertionError: If the response status code is not 409.
    """
    password = "SuperSecure!Pwd123"
    response = dioptra_client.users.create(
        username=non_existing_username, email=existing_email, password=password
    )
    assert response.status_code == HTTPStatus.CONFLICT


def assert_user_username_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    user_id: int,
    expected_name: str,
) -> None:
    """Assert that the name of a user matches the expected name.

    Args:
        dioptra_client: The Dioptra client.
        user_id: The id of the user to retrieve.
        expected_name: The expected name of the user.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            user does not match the expected name.
    """
    response = dioptra_client.users.get_by_id(user_id)
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["name"] == expected_name
    )


def assert_current_user_username_matches_expected_name(
    dioptra_client: DioptraClient[DioptraResponseProtocol], expected_name: str
) -> None:
    """Assert that the name of the current user matches the expected name.

    Args:
        dioptra_client: The Dioptra client.
        expected_name: The expected name of the user.

    Raises:
        AssertionError: If the response status code is not 200 or if the name of the
            user does not match the expected name.
    """
    response = dioptra_client.users.get_current()
    assert (
        response.status_code == HTTPStatus.OK
        and response.json()["name"] == expected_name
    )


def assert_user_is_not_found(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    user_id: int,
) -> None:
    """Assert that a user is not found.

    Args:
        dioptra_client: The Dioptra client.
        user_id: The id of the user to retrieve.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.users.get_by_id(user_id)
    assert response.status_code == HTTPStatus.NOT_FOUND


def assert_cannot_rename_user_with_existing_username(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    existing_username: str,
) -> None:
    """Assert that renaming a user with an existing username fails.

    Args:
        dioptra_client: The Dioptra client.
        existing_username: The username of the existing user.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.users.modify_current_user(
        username=existing_username,
        email="new_email",
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_cannot_rename_user_with_existing_email(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    existing_email: str,
) -> None:
    """Assert that changing a user email with an existing email fails.

    Args:
        dioptra_client: The Dioptra client.
        existing_email: The email of the existing user.

    Raises:
        AssertionError: If the response status code is not 400.
    """
    response = dioptra_client.users.modify_current_user(
        username="new_username",
        email=existing_email,
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def assert_login_works(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    username: str,
    password: str,
):
    """Assert that logging in using a username and password works.

    Args:
        dioptra_client: The Dioptra client.
        username: The username of the user to be logged in.
        password: The password of the user to be logged in.

    Raises:
        AssertionError: If the response status code is not 200.
    """
    assert dioptra_client.auth.login(username, password).status_code == HTTPStatus.OK


def assert_user_does_not_exist(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    username: str,
    password: str,
):
    """Assert that the user does not exist.

    Args:
        dioptra_client: The Dioptra client.
        username: The username of the user to be logged in.
        password: The password of the user to be logged in.

    Raises:
        AssertionError: If the response status code is not 404.
    """
    response = dioptra_client.auth.login(username, password)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def assert_login_is_unauthorized(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    username: str,
    password: str,
):
    """Assert that logging in using a username and password is unauthorized.

    Args:
        dioptra_client: The Dioptra client.
        username: The username of the user to be logged in.
        password: The password of the user to be logged in.

    Raises:
        AssertionError: If the response status code is not 401.
    """
    response = dioptra_client.auth.login(username, password)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def assert_new_password_cannot_be_existing(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    password: str,
    user_id: str | None = None,
):
    """Assert that changing a user (current or otherwise) password to the
    existing password fails.

    Args:
        client (FlaskClient): The Flask test client.
        password (str): The existing password of the user.
        user_id (str, optional): The user id. If this is not passed,
        we assume we are the current user. Defaults to None.

    Raises:
        AssertionError: If the response status code is not 403.
    """
    # Means we are the current user.
    if user_id is None:
        response = dioptra_client.users.change_current_user_password(password, password)
        assert response.status_code == HTTPStatus.FORBIDDEN
    else:
        response = dioptra_client.users.change_password_by_id(
            user_id, password, password
        )
        assert response.status_code == HTTPStatus.FORBIDDEN


# -- Tests -------------------------------------------------------------


def test_create_user(dioptra_client: DioptraClient[DioptraResponseProtocol]) -> None:
    """Test that we can create a user and its response is expected.

    This test validates the following sequence of actions:

    - Register a new user using the username, email, and password.
    - Assert that the response matches what we expect to see, i.e. CurrentUser
    schema information.
    - Login with the user that we just created.
    - Assert that retrieving the current user works.
    - Finally, assert that we can retrieve the current user by ID and it matches
    our expectations.
    """
    username = "user"
    email = "user@example.org"
    password = "SuperSecure!Pwd123"

    # Posting a user returns CurrentUserSchema.
    user_response = dioptra_client.users.create(username, email, password).json()
    assert_user_response_contents_matches_expectations(
        response=user_response,
        expected_contents={
            "username": username,
            "email": email,
        },
        current_user=True,
    )

    dioptra_client.auth.login(username, password)
    assert_retrieving_current_user_works(dioptra_client, expected=user_response)

    # Getting a user by id returns UserSchema.
    user_expected = {
        k: v for k, v in user_response.items() if k in ["username", "email", "id"]
    }
    assert_retrieving_user_by_id_works(
        dioptra_client, user_expected["id"], user_expected
    )


def test_user_get_all(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
) -> None:
    """Test that all users can be retrieved.

    Given an authenticated user and registered users, this test validates the following
    sequence of actions:

    - Three users are registered, "user1", "user2", "user3".
    - The user is able to retrieve a list of all registered users.
    - The returned list of users matches the full list of registered users.
    """
    user_expected_list = [
        {"username": user["username"], "email": user["email"], "id": user["id"]}
        for user in list(registered_users.values())
    ]
    assert_retrieving_users_works(dioptra_client, expected=user_expected_list)


def test_user_search_query(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
) -> None:
    """Test that users can be found using a search query.

    Given an authenticated user and registered users, this test validates the following
    sequence of actions:

    - The user is able to retrieve a list of all users that match the query.
    - The returned list of users matches the expected matches from the query.
    """
    user_expected_list = [
        {"username": user["username"], "email": user["email"], "id": user["id"]}
        for user in list(registered_users.values())[:2]
    ]
    assert_retrieving_users_works(
        dioptra_client, expected=user_expected_list, search="username:*user*"
    )
    assert_retrieving_users_works(
        dioptra_client, expected=user_expected_list, search="username:'*user*'"
    )
    assert_retrieving_users_works(
        dioptra_client, expected=user_expected_list, search='username:"user?"'
    )
    assert_retrieving_users_works(
        dioptra_client, expected=user_expected_list, search="username:user?,email:user*"
    )
    assert_retrieving_users_works(
        dioptra_client, expected=[], search=r"username:\*user*"
    )
    assert_retrieving_users_works(dioptra_client, expected=[], search="email:user?")


def test_cannot_register_existing_username(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    registered_users: dict[str, Any],
) -> None:
    """Test that registering a user with an existing username fails.

    Given an authenticated user and registered users, this test validates the following
    sequence of actions:

    - One user is registered, "user1".
    - A new user is registered with the same email as user1, a different username.
    - The request fails with an appropriate error message and response code.
    """
    existing_user = registered_users["user1"]
    assert_registering_existing_username_fails(
        dioptra_client,
        existing_username=existing_user["username"],
        non_existing_email="unique" + existing_user["email"],
    )


def test_cannot_register_existing_email(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    registered_users: dict[str, Any],
) -> None:
    """Test that registering a user with an existing email fails.

    Given an authenticated user and registered users, this test validates the following
    sequence of actions:

    - One user is registered, "user1".
    - A new user is registered with the same email as user1, but _not_ the same email.
    - The request fails with an appropriate error message and response code.
    """
    existing_user = registered_users["user1"]
    assert_registering_existing_email_fails(
        dioptra_client,
        non_existing_username="unique" + existing_user["username"],
        existing_email=existing_user["email"],
    )


def test_rename_current_user(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
) -> None:
    """Test that renaming the current user works.

    Given an authenticated user, this test validates the following sequence of actions:

    - A user modifies its username and we record the response from the API.
    - Retrieving the current user works and responds with the response we recorded
    that reflects the updated username.
    """
    new_username = "new_name"
    user = dioptra_client.users.modify_current_user(
        username=new_username,
        email=auth_account["email"],
    ).json()
    assert_retrieving_current_user_works(dioptra_client, expected=user)


def test_user_authorization_failure(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    registered_users: dict[str, Any],
) -> None:
    """Test that a user providing an incorrect password cannot log in.

    Given an authenticated user, this test validates the following sequence of actions:

    - The current attempts to login with an incorrect password.
    - The user cannot log in.
    """
    username = registered_users["user2"]["username"]
    password = registered_users["user2"]["password"] + "incorrect"
    assert_login_is_unauthorized(dioptra_client, username=username, password=password)


def test_delete_current_user(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
) -> None:
    """Test that deleting the current user works.

    Given an authenticated user, this test validates the following sequence of actions:

    - The current user deletes itself using its password.
    - The user can no longer log in.
    """
    username = auth_account["username"]
    password = auth_account["password"]
    dioptra_client.users.delete_current_user(password)
    assert_user_does_not_exist(dioptra_client, username=username, password=password)


def test_change_current_user_password(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
):
    """Test that changing the current user password works.

    Given an authenticated user, this test validates the following sequence of actions:

    - The current user changes its password, and it does not fail.
    - The current user is able to login with the new password.
    """
    username = auth_account["username"]
    old_password = auth_account["password"]
    new_password = "NewSecure!Pwd456789"
    dioptra_client.users.change_current_user_password(old_password, new_password)
    assert_login_works(dioptra_client, username=username, password=new_password)


def test_change_user_password(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    registered_users: dict[str, Any],
):
    """Test that changing a user password works.

    Given an authenticated user, this test validates the following sequence of actions:

    - Using its ID, a user's password is changed, and it does not fail.
    - This user is then able to login with the new password.
    """
    user_id = registered_users["user2"]["id"]
    username = registered_users["user2"]["username"]
    old_password = registered_users["user2"]["password"]
    new_password = "NewSecure!Pwd456789"
    dioptra_client.users.change_password_by_id(user_id, old_password, new_password)
    assert_login_works(dioptra_client, username=username, password=new_password)


def test_new_password_cannot_be_existing(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
):
    """Test that changing a password and setting the new password as the
    old password fails.

    Given an authenticated user, this test validates the following sequence of actions:

    - The current user tries to set its new password which is the same as its existing
    password and this action fails.
    - The same password as the existing password for a user with an ID is attempted
    to be set and this action fails.
    """
    user_id = auth_account["id"]
    password = auth_account["password"]
    # test via /users/current
    assert_new_password_cannot_be_existing(dioptra_client, password)
    # test via /users/{user_id}
    assert_new_password_cannot_be_existing(dioptra_client, password, user_id)


def test_cannot_register_with_weak_password(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
) -> None:
    """Test that registering with a password that fails complexity rules is rejected."""
    response = dioptra_client.users.create(
        username="weakpwuser",
        email="weakpwuser@example.org",
        password="weakpass",
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


@freeze_time("Apr 1st, 2025 6:00am", auto_tick_seconds=1)
def test_account_is_locked_after_repeated_failed_logins(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    registered_users: dict[str, Any],
) -> None:
    """Test that repeated failed login attempts lock the account.

    The default lockout threshold is 5 failed attempts; after that, a correct
    password should still be rejected with UNAUTHORIZED until the lockout expires.
    """
    user = registered_users["user2"]
    username = user["username"]
    correct_password = user["password"]
    wrong_password = correct_password + "-wrong"

    for _ in range(5):
        response = dioptra_client.auth.login(username, wrong_password)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    # Account should now be locked; even the correct password is rejected.
    locked_response = dioptra_client.auth.login(username, correct_password)
    assert locked_response.status_code == HTTPStatus.UNAUTHORIZED

    # Security regression: the response MUST NOT leak the username or the
    # lockout expiry timestamp (would enable enumeration + lets a credential
    # stuffer know the exact moment the lockout expires). It must also be
    # indistinguishable from a plain wrong-password 401.
    body = locked_response.json()
    assert "username" not in body.get("detail", {})
    assert "locked_until" not in body.get("detail", {})
    message = body.get("message", "")
    assert username not in message
    assert "locked" not in message.lower()
    assert "until" not in message.lower()
    # The serialized ``error`` field is ``error.__class__.__name__``; if the
    # handler passes an ``AccountLockedError`` through directly, an attacker
    # can read ``"AccountLockedError"`` here and distinguish lockout from
    # wrong-password responses. The handler must forward a generic
    # ``UserPasswordError`` so the class name matches a plain 401.
    error_field = body.get("error", "")
    assert "Locked" not in error_field
    assert "Account" not in error_field


@freeze_time("Apr 1st, 2025 6:30am", auto_tick_seconds=1)
def test_successful_login_resets_failed_attempts(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    registered_users: dict[str, Any],
) -> None:
    """Test that a successful login clears the failed_login_attempts counter."""
    user = registered_users["user2"]
    username = user["username"]
    correct_password = user["password"]
    wrong_password = correct_password + "-wrong"

    # A few bad attempts...
    for _ in range(3):
        assert (
            dioptra_client.auth.login(username, wrong_password).status_code
            == HTTPStatus.UNAUTHORIZED
        )

    # ...then a good one resets the counter.
    assert (
        dioptra_client.auth.login(username, correct_password).status_code
        == HTTPStatus.OK
    )

    # We can fail up to the threshold again without being locked out on the next try.
    for _ in range(4):
        assert (
            dioptra_client.auth.login(username, wrong_password).status_code
            == HTTPStatus.UNAUTHORIZED
        )
    assert (
        dioptra_client.auth.login(username, correct_password).status_code
        == HTTPStatus.OK
    )


def test_lockout_expiry_grants_fresh_attempt_window(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    registered_users: dict[str, Any],
) -> None:
    """After a lockout window elapses, a single wrong password must NOT immediately re-lock.

    Regression test: previously the counter stayed at 5 after expiry, so the
    first post-expiry wrong attempt bumped it to 6 >= max_attempts and the
    account was re-locked with zero tolerance.
    """
    user = registered_users["user3"]
    username = user["username"]
    correct_password = user["password"]
    wrong_password = "BadGuess!Attempt2025"

    with freeze_time("Apr 1st, 2025 8:00am", auto_tick_seconds=1):
        for _ in range(5):
            assert (
                dioptra_client.auth.login(username, wrong_password).status_code
                == HTTPStatus.UNAUTHORIZED
            )
        # account is now locked
        assert (
            dioptra_client.auth.login(username, correct_password).status_code
            == HTTPStatus.UNAUTHORIZED
        )

    # Advance well past the 30-min default lockout window.
    with freeze_time("Apr 1st, 2025 9:30am", auto_tick_seconds=1):
        # A single wrong attempt after expiry must NOT immediately re-lock.
        assert (
            dioptra_client.auth.login(username, wrong_password).status_code
            == HTTPStatus.UNAUTHORIZED
        )
        # The counter was reset on expiry, so the correct password still works.
        assert (
            dioptra_client.auth.login(username, correct_password).status_code
            == HTTPStatus.OK
        )


def test_expired_password_does_not_trigger_lockout(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    registered_users: dict[str, Any],
) -> None:
    """An expired-but-correct password must not count as a failed login attempt.

    Regression test: previously UserPasswordService.authenticate() raised the
    same UserPasswordError for both wrong-password and expired-password cases,
    so an expired correct password would increment failed_login_attempts and
    eventually lock the account.
    """
    user = registered_users["user2"]
    username = user["username"]
    correct_password = user["password"]

    # Jump more than a year forward so password_expire_on (now + 1 year) is past.
    response = None
    with freeze_time("Jan 1st, 2027 12:00pm", auto_tick_seconds=1):
        for _ in range(7):
            response = dioptra_client.auth.login(username, correct_password)
            assert response.status_code == HTTPStatus.UNAUTHORIZED

        # Account must NOT be locked — counter should not have moved.
        assert response is not None
        body = response.json()
        assert "locked" not in body.get("message", "").lower()


def test_password_change_rejects_weak_password(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
) -> None:
    """Test that changing the password to one that fails complexity rules is rejected."""
    response = dioptra_client.users.change_current_user_password(
        auth_account["password"], "short"
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


@freeze_time("Apr 1st, 2025 7:00am", auto_tick_seconds=1)
def test_password_change_rejects_reused_history(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
) -> None:
    """Test that changing the password to a previously used password is rejected."""
    original_password = auth_account["password"]
    next_password = "Rotated!Password2025"

    # Rotate to a new password...
    assert (
        dioptra_client.users.change_current_user_password(
            original_password, next_password
        ).status_code
        == HTTPStatus.OK
    )

    # ...then log back in with the new password so we have a valid session.
    assert (
        dioptra_client.auth.login(auth_account["username"], next_password).status_code
        == HTTPStatus.OK
    )

    # Attempting to roll back to the original password must be rejected.
    response = dioptra_client.users.change_current_user_password(
        next_password, original_password
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


@freeze_time("Apr 1st, 2025 7:30am", auto_tick_seconds=1)
def test_password_history_retains_full_depth_after_many_rotations(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    auth_account: dict[str, Any],
    monkeypatch: Any,
) -> None:
    """Regression: history must not be prematurely trimmed.

    The initial Phase 1 implementation double-added each new entry to the
    ``user.password_history`` collection (once via SQLAlchemy's
    ``back_populates`` on construction, then again via an explicit
    ``list.insert(0, entry)``). Combined with ``cascade=delete-orphan`` on
    the ``User.password_history`` relationship, the inflated list length
    caused the trim step to mark valid, still-in-window history rows as
    orphans and delete them from the database.

    This test shrinks ``PASSWORD_HISTORY_DEPTH`` so a few rotations are
    enough to cross the trim threshold, then verifies that:

    1. Every password within the depth window is still blocked on reuse.
    2. The oldest password, which SHOULD be outside the window after
       rotation, is accepted again — proving the trim itself works but is
       not over-eager.
    """
    from dioptra.restapi.v1.users import service as users_service

    monkeypatch.setattr(users_service, "PASSWORD_HISTORY_DEPTH", 3)

    current = auth_account["password"]
    rotations = [
        "Rotation!NumberOne2025",
        "Rotation!NumberTwo2025",
        "Rotation!NumberThree2025",
        "Rotation!NumberFour2025",
    ]

    # Walk through 4 rotations with depth=3 (buggy code would orphan-delete
    # entries during this sequence).
    for pwd in rotations:
        assert (
            dioptra_client.users.change_current_user_password(
                current, pwd
            ).status_code
            == HTTPStatus.OK
        )
        assert (
            dioptra_client.auth.login(
                auth_account["username"], pwd
            ).status_code
            == HTTPStatus.OK
        )
        current = pwd

    # The last 3 in-window passwords (the starting password is now out of
    # window) MUST be blocked on reuse.
    for in_window in rotations[:3]:
        response = dioptra_client.users.change_current_user_password(
            current, in_window
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f"Expected reuse of in-window password {in_window!r} to be "
            f"rejected with 403, got {response.status_code}. This means the "
            f"history was prematurely trimmed."
        )

    # The original password is now OUT of the 3-deep window, so it must be
    # accepted again. (If it weren't, the trim would be broken in the other
    # direction — never letting anything out of history.)
    assert (
        dioptra_client.users.change_current_user_password(
            current, auth_account["password"]
        ).status_code
        == HTTPStatus.OK
    )
