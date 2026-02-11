"""Tests for input validation functions."""

from web.validation import validate_activity_id, validate_boolean, validate_integer

# ============================================================================
# validate_activity_id
# ============================================================================


def test_validate_activity_id_valid():
    """Valid activity IDs should pass."""
    assert validate_activity_id("fishing")[0] is True
    assert validate_activity_id("online_3h")[0] is True
    assert validate_activity_id("a")[0] is True


def test_validate_activity_id_empty():
    """Empty/None should fail."""
    is_valid, msg = validate_activity_id(None)
    assert is_valid is False
    assert "Missing" in msg

    is_valid, msg = validate_activity_id("")
    assert is_valid is False


def test_validate_activity_id_not_string():
    """Non-string types should fail."""
    is_valid, msg = validate_activity_id(123)
    assert is_valid is False
    assert "string" in msg


def test_validate_activity_id_special_chars():
    """Special characters (except underscore) should fail."""
    is_valid, msg = validate_activity_id("fish-ing")
    assert is_valid is False
    assert "Invalid" in msg

    is_valid, msg = validate_activity_id("fish ing")
    assert is_valid is False

    is_valid, msg = validate_activity_id("fish@ing")
    assert is_valid is False


def test_validate_activity_id_too_long():
    """IDs longer than 50 chars should fail."""
    is_valid, msg = validate_activity_id("a" * 51)
    assert is_valid is False
    assert "too long" in msg

    # Exactly 50 should pass
    assert validate_activity_id("a" * 50)[0] is True


# ============================================================================
# validate_boolean
# ============================================================================


def test_validate_boolean_native():
    """Native booleans should pass through."""
    is_valid, value, _ = validate_boolean(True, "field")
    assert is_valid is True
    assert value is True

    is_valid, value, _ = validate_boolean(False, "field")
    assert is_valid is True
    assert value is False


def test_validate_boolean_strings():
    """String representations should be converted."""
    for truthy in ("true", "True", "TRUE", "1", "yes"):
        is_valid, value, _ = validate_boolean(truthy, "field")
        assert is_valid is True
        assert value is True

    for falsy in ("false", "False", "FALSE", "0", "no"):
        is_valid, value, _ = validate_boolean(falsy, "field")
        assert is_valid is True
        assert value is False


def test_validate_boolean_integers():
    """Integer values should be converted."""
    is_valid, value, _ = validate_boolean(1, "field")
    assert is_valid is True
    assert value is True

    is_valid, value, _ = validate_boolean(0, "field")
    assert is_valid is True
    assert value is False


def test_validate_boolean_none():
    """None should fail with field name in message."""
    is_valid, _, msg = validate_boolean(None, "vip_status")
    assert is_valid is False
    assert "vip_status" in msg


def test_validate_boolean_invalid():
    """Invalid types should fail."""
    is_valid, _, msg = validate_boolean([1, 2], "field")
    assert is_valid is False
    assert "boolean" in msg


# ============================================================================
# validate_integer
# ============================================================================


def test_validate_integer_valid():
    """Valid integers should pass."""
    is_valid, value, _ = validate_integer(42, "amount")
    assert is_valid is True
    assert value == 42


def test_validate_integer_string_number():
    """String numbers should be converted."""
    is_valid, value, _ = validate_integer("100", "amount")
    assert is_valid is True
    assert value == 100


def test_validate_integer_none():
    """None should fail."""
    is_valid, _, msg = validate_integer(None, "amount")
    assert is_valid is False
    assert "Missing" in msg


def test_validate_integer_non_numeric():
    """Non-numeric strings should fail."""
    is_valid, _, msg = validate_integer("abc", "amount")
    assert is_valid is False
    assert "number" in msg


def test_validate_integer_below_min():
    """Values below min should fail."""
    is_valid, _, msg = validate_integer(-1, "amount", min_val=0)
    assert is_valid is False
    assert "less than" in msg


def test_validate_integer_above_max():
    """Values above max should fail."""
    is_valid, _, msg = validate_integer(1000001, "amount", max_val=1000000)
    assert is_valid is False
    assert "exceed" in msg


def test_validate_integer_at_boundaries():
    """Values exactly at min/max should pass."""
    assert validate_integer(0, "amount", min_val=0)[0] is True
    assert validate_integer(1000000, "amount", max_val=1000000)[0] is True
