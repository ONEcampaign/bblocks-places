"""Tests for the resolver module."""

import pytest

from bblocks.places import resolver
from bblocks.places.config import PlaceNotFoundError, MultipleCandidatesError

# ----------------------------------------
# Tests for the handle_not_founds function
# ----------------------------------------

def test_handle_not_founds_raises_when_none_and_raise():
    """Raises if a candidate is None and not_found='raise'."""
    candidates = {"A": None, "B": "value"}
    with pytest.raises(PlaceNotFoundError):
        resolver.handle_not_founds(candidates, not_found="raise")


def test_handle_not_founds_ignore_keeps_none():
    """Keeps None values when not_found='ignore'."""
    candidates = {"A": None, "B": "value"}
    result = resolver.handle_not_founds(candidates.copy(), not_found="ignore")
    assert result == {"A": None, "B": "value"}


def test_handle_not_founds_replaces_none_with_custom_string():
    """Replaces None values with the provided not_found string."""
    candidates = {"A": None, "B": "value"}
    result = resolver.handle_not_founds(candidates.copy(), not_found="MISSING")
    assert result == {"A": "MISSING", "B": "value"}


# ----------------------------------------
# Tests for the handle_multiple_candidates function
# ----------------------------------------

def test_handle_multiple_candidates_raise_error_on_list():
    """Raises when multiple_candidates='raise' and a candidate is a list."""
    candidates = {"A": ["x","y"], "B": "single"}
    with pytest.raises(MultipleCandidatesError):
        resolver.handle_multiple_candidates(candidates, multiple_candidates="raise")

def test_handle_multiple_candidates_first_picks_first():
    """Selects the first element when multiple_candidates='first'."""
    candidates = {"A": ["x","y"], "B": ["u","v"], "C": "only"}
    result = resolver.handle_multiple_candidates(candidates.copy(), multiple_candidates="first")
    assert result == {"A": "x", "B": "u", "C": "only"}

def test_handle_multiple_candidates_last_picks_last():
    """Selects the last element when multiple_candidates='last'."""
    candidates = {"A": ["x","y"], "B": ["u","v"], "C": "only"}
    result = resolver.handle_multiple_candidates(candidates.copy(), multiple_candidates="last")
    assert result == {"A": "y", "B": "v", "C": "only"}

def test_handle_multiple_candidates_ignore_keeps_lists():
    """Keeps list values when multiple_candidates='ignore'."""
    candidates = {"A": ["x","y"], "B": ["u"], "C": "only"}
    result = resolver.handle_multiple_candidates(candidates.copy(), multiple_candidates="ignore")
    assert result == {"A": ["x","y"], "B": ["u"], "C": "only"}

def test_handle_multiple_candidates_invalid_option_raises_value_error():
    """Raises ValueError for an unsupported multiple_candidates option."""
    candidates = {"A": ["x","y"], "B": "single"}
    with pytest.raises(ValueError):
        resolver.handle_multiple_candidates(candidates, multiple_candidates="unsupported")

# ----------------------------------------
# Tests for the handle_missing_values function
# ----------------------------------------

def test_handle_missing_values_logs_warning_for_none_values(caplog):
    """Warns when a candidate is None but dcid_map has a non-null value."""
    candidates = {"A": None, "B": None}
    dcid_map = {"A": "dcidA", "B": None}
    caplog.set_level("WARNING")
    result = resolver.handle_missing_values(candidates.copy(), dcid_map, to_type="test")
    assert "No value found for 'A' when mapping to 'test'" in caplog.text
    # candidates dict should remain unchanged
    assert result == {"A": None, "B": None}

def test_handle_missing_values_no_warning_when_dcid_missing(caplog):
    """No warning if dcid_map entry is None, even when candidate is None."""
    candidates = {"A": None}
    dcid_map = {"A": None}
    caplog.set_level("WARNING")
    result = resolver.handle_missing_values(candidates.copy(), dcid_map, to_type="foo")
    assert caplog.text == ""
    assert result == {"A": None}

def test_handle_missing_values_no_warning_for_non_none_values(caplog):
    """No warning when candidate value is present."""
    candidates = {"A": "value"}
    dcid_map = {"A": "dcidA"}
    caplog.set_level("WARNING")
    result = resolver.handle_missing_values(candidates.copy(), dcid_map, to_type="bar")
    assert caplog.text == ""
    assert result == {"A": "value"}


# ----------------------------------------
# Tests for the read_default_concordance_table function
# ----------------------------------------

def test_read_default_concordance_table_has_exact_columns():
    """Ensure DataFrame columns exactly match DEFAULT_CONCORDANCE_DTYPES keys."""
    df = resolver.read_default_concordance_table()
    expected = set(resolver.DEFAULT_CONCORDANCE_DTYPES.keys())
    assert set(df.columns) == expected, f"Got columns: {df.columns.tolist()}"
    assert len(df.columns) == len(expected)
