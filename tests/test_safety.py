import pytest

from app.core.safety import is_protected, validate_disable_request


def test_tv_input_is_protected() -> None:
    assert is_protected("com.mediatek.tvinput")


def test_unrelated_package_is_not_protected() -> None:
    assert not is_protected("com.example.demo")


def test_protected_package_cannot_be_disabled() -> None:
    with pytest.raises(PermissionError):
        validate_disable_request("com.mediatek.wwtv.tvcenter")


def test_empty_package_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_disable_request("   ")
