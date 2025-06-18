"""Tests for the main module."""

import pytest
import pandas as pd

from bblocks.places import main


# ----------------------------------------------
# Tests for get_default_concordance_table
# ----------------------------------------------

def test_get_default_concordance_table_returns_internal_table(monkeypatch):
    """get_default_concordance_table() should return whatever the internal resolver’s table is."""
    dummy = pd.DataFrame({"dcid": ["X"], "region": ["R1"]})
    # Inject our dummy into the internal resolver
    monkeypatch.setattr(main._country_resolver, "_concordance_table", dummy)
    assert main.get_default_concordance_table() is dummy

@pytest.mark.parametrize("fmt", ["dcid", "name_official", "iso3_code"])
def test_validate_place_format_accepts_valid_formats(fmt):
    """_validate_place_format should accept any known source formats without error."""
    # should not raise
    main._validate_place_format(fmt)

def test_validate_place_format_rejects_invalid_format():
    """_validate_place_format should raise ValueError on invalid formats."""
    with pytest.raises(ValueError) as exc:
        main._validate_place_format("not_a_valid_format")
    assert "Invalid place format" in str(exc.value)

@pytest.mark.parametrize("tgt", ["region", "subregion", "income_level"])
def test_validate_place_target_accepts_valid_targets(tgt):
    """_validate_place_target should accept known target fields without error."""
    # should not raise
    main._validate_place_target(tgt)

def test_validate_place_target_rejects_invalid_target():
    """_validate_place_target should raise ValueError on invalid targets."""
    with pytest.raises(ValueError) as exc:
        main._validate_place_target("not_a_valid_target")
    # it currently uses the same wording as format errors
    assert "Invalid place format" in str(exc.value)