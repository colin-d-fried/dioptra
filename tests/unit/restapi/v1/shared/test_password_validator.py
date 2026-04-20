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
"""Unit tests for the PasswordValidator module."""

import pytest

from dioptra.restapi.v1.shared.password_validator import (
    PasswordComplexityError,
    PasswordValidator,
)


def test_accepts_strong_password():
    validator = PasswordValidator()
    # 18 chars, all four character classes, not in blocklist, not matching user info.
    validator.validate(
        password="StrongPassword!42",
        username="alice",
        email_address="alice@example.com",
    )


def test_rejects_short_password():
    validator = PasswordValidator()
    with pytest.raises(PasswordComplexityError) as excinfo:
        validator.validate(password="Short!1", username="u", email_address="u@x.org")
    assert any("at least" in r for r in excinfo.value.reasons)


def test_rejects_missing_uppercase():
    validator = PasswordValidator()
    with pytest.raises(PasswordComplexityError) as excinfo:
        validator.validate(
            password="no-upper-letters!42",
            username="u",
            email_address="u@x.org",
        )
    assert any("uppercase" in r for r in excinfo.value.reasons)


def test_rejects_missing_lowercase():
    validator = PasswordValidator()
    with pytest.raises(PasswordComplexityError) as excinfo:
        validator.validate(
            password="NO-LOWER-LETTERS!42",
            username="u",
            email_address="u@x.org",
        )
    assert any("lowercase" in r for r in excinfo.value.reasons)


def test_rejects_missing_digit():
    validator = PasswordValidator()
    with pytest.raises(PasswordComplexityError) as excinfo:
        validator.validate(
            password="NoDigitsPresent!!",
            username="u",
            email_address="u@x.org",
        )
    assert any("digit" in r for r in excinfo.value.reasons)


def test_rejects_missing_special_character():
    validator = PasswordValidator()
    with pytest.raises(PasswordComplexityError) as excinfo:
        validator.validate(
            password="NoSpecialChar1234",
            username="u",
            email_address="u@x.org",
        )
    assert any("special" in r for r in excinfo.value.reasons)


def test_rejects_password_matching_username():
    validator = PasswordValidator()
    with pytest.raises(PasswordComplexityError) as excinfo:
        validator.validate(
            password="Administrator!1",
            username="Administrator!1",
            email_address="a@x.org",
        )
    assert any("username" in r.lower() for r in excinfo.value.reasons)


def test_rejects_password_matching_email_local_part():
    validator = PasswordValidator()
    with pytest.raises(PasswordComplexityError) as excinfo:
        validator.validate(
            password="MySecretPass!123",
            username="someone_else",
            email_address="MySecretPass!123@example.org",
        )
    assert any("email" in r.lower() for r in excinfo.value.reasons)


def test_rejects_common_blocklisted_password():
    validator = PasswordValidator(blocklist={"MyCompanyPass!1"})
    with pytest.raises(PasswordComplexityError) as excinfo:
        validator.validate(
            password="MyCompanyPass!1",
            username="alice",
            email_address="alice@example.com",
        )
    assert any("common" in r.lower() for r in excinfo.value.reasons)


def test_aggregates_multiple_failures():
    validator = PasswordValidator()
    with pytest.raises(PasswordComplexityError) as excinfo:
        validator.validate(
            password="short",
            username="bob",
            email_address="bob@example.com",
        )
    # Expect at least 3 distinct complaints (length, uppercase, digit, special).
    assert len(excinfo.value.reasons) >= 3


def test_respects_configured_min_length():
    validator = PasswordValidator(min_length=8)
    validator.validate(
        password="Aa1!abcd",
        username="bob",
        email_address="bob@example.com",
    )


def test_rejects_invalid_min_length():
    with pytest.raises(ValueError):
        PasswordValidator(min_length=0)
