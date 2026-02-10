"""Input validation and API response helpers."""

from typing import Any, Optional

from flask import Response, jsonify


def api_success(**data: Any) -> Response:
    """Return a standardized API success response."""
    return jsonify({"success": True, **data})


def api_error(message: str, status_code: int = 400) -> tuple[Response, int]:
    """Return a standardized API error response."""
    return jsonify({"success": False, "error": message}), status_code


def validate_activity_id(value: Any) -> tuple[bool, str]:
    """Validate activity_id format.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value:
        return False, "Missing activity_id"
    if not isinstance(value, str):
        return False, "activity_id must be a string"
    if not all(c.isalnum() or c == "_" for c in value):
        return False, "Invalid activity_id format"
    if len(value) > 50:
        return False, "activity_id too long"
    return True, ""


def validate_boolean(value: Any, field_name: str) -> tuple[bool, bool, str]:
    """Validate and convert a boolean field.

    Returns:
        Tuple of (is_valid, converted_value, error_message)
    """
    if value is None:
        return False, False, f"Missing {field_name}"
    if isinstance(value, bool):
        return True, value, ""
    if isinstance(value, str):
        if value.lower() in ("true", "1", "yes"):
            return True, True, ""
        if value.lower() in ("false", "0", "no"):
            return True, False, ""
    if isinstance(value, int):
        return True, bool(value), ""
    return False, False, f"{field_name} must be a boolean"


def validate_integer(
    value: Any,
    field_name: str,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
) -> tuple[bool, int, str]:
    """Validate and convert an integer field.

    Returns:
        Tuple of (is_valid, converted_value, error_message)
    """
    if value is None:
        return False, 0, f"Missing {field_name}"

    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return False, 0, f"{field_name} must be a number"

    if min_val is not None and int_value < min_val:
        return False, 0, f"{field_name} cannot be less than {min_val}"
    if max_val is not None and int_value > max_val:
        return False, 0, f"{field_name} cannot exceed {max_val}"

    return True, int_value, ""
