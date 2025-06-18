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


# ----------------------------------------------
# Tests for resolve function
# ----------------------------------------------


def test_resolve_delegates_to_country_resolver(monkeypatch):
    """main.resolve should pass all arguments through to _country_resolver.resolve."""
    # Capture the kwargs passed to the resolver
    captured = {}
    def fake_resolve(**kwargs):
        captured.update(kwargs)
        return ["RESULT"]
    monkeypatch.setattr(main._country_resolver, "resolve", fake_resolve)

    places = ["Alpha", "Beta"]
    out = main.resolve(
        places,
        from_type="name_official",
        to_type="region",
        not_found="ignore",
        multiple_candidates="first",
        custom_mapping={"Alpha": "X"},
        ignore_nulls=False
    )

    assert out == ["RESULT"]
    assert captured["places"] == places
    assert captured["from_type"] == "name_official"
    assert captured["to_type"] == "region"
    assert captured["not_found"] == "ignore"
    assert captured["multiple_candidates"] == "first"
    assert captured["custom_mapping"] == {"Alpha": "X"}
    assert captured["ignore_nulls"] is False

def test_resolve_invalid_from_type_raises_before_delegate():
    """main.resolve should validate from_type and raise on invalid values."""
    with pytest.raises(ValueError):
        main.resolve(["A"], from_type="not_a_format")


# ----------------------------------------------
# Tests for _validate_filter_values
# ----------------------------------------------
def test_validate_filter_values_accepts_single_value(monkeypatch):
    """_validate_filter_values accepts a single-item list when valid."""
    dummy = pd.DataFrame({
        'dcid': ['x1', 'x2'],
        'region': ['Asia', 'Europe']
    })
    monkeypatch.setattr(main._country_resolver, '_concordance_table', dummy)
    # Pass as a list so it iterates correctly
    main._validate_filter_values('region', ['Asia'])

def test_validate_filter_values_accepts_list_of_values(monkeypatch):
    """_validate_filter_values accepts a list of strings all present in the table."""
    dummy = pd.DataFrame({
        'dcid': ['x1', 'x2', 'x3'],
        'income_level': ['High income', 'Low income', 'Lower middle income']
    })
    monkeypatch.setattr(main._country_resolver, '_concordance_table', dummy)
    main._validate_filter_values('income_level', ['High income', 'Low income'])

def test_validate_filter_values_rejects_invalid_value(monkeypatch):
    """_validate_filter_values raises ValueError if any value is not in the valid set."""
    dummy = pd.DataFrame({
        'dcid': ['x1'],
        'subregion': ['Southern Asia']
    })
    monkeypatch.setattr(main._country_resolver, '_concordance_table', dummy)
    with pytest.raises(ValueError) as exc:
        main._validate_filter_values('subregion', ['Southern Asia', 'Atlantis'])
    assert "Invalid filter values" in str(exc.value)