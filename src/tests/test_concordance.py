"""Tests for the concordance module."""

import pandas as pd
import pytest

from bblocks.places import concordance

def test_missing_dcid_column_raises():
    df = pd.DataFrame({"foo": [1, 2, 3]})
    with pytest.raises(ValueError) as exc:
        concordance.validate_concordance_table(df)
    assert "must have a column named 'dcid'" in str(exc.value)


def test_empty_table_raises():
    # Has 'dcid' but zero rows
    df = pd.DataFrame({"dcid": pd.Series(dtype=str), "other": pd.Series(dtype=int)})
    with pytest.raises(ValueError) as exc:
        concordance.validate_concordance_table(df)
    assert "must have at least one row" in str(exc.value)


def test_null_values_in_dcid_raises():
    df = pd.DataFrame({
        "dcid": ["a", None, "c"],
        "other": [1, 2, 3],
    })
    with pytest.raises(ValueError) as exc:
        concordance.validate_concordance_table(df)
    assert "must not contain null values" in str(exc.value)


def test_duplicate_dcid_values_raises():
    df = pd.DataFrame({
        "dcid": ["x", "x", "y"],
        "other": [1, 2, 3],
    })
    with pytest.raises(ValueError) as exc:
        concordance.validate_concordance_table(df)
    assert "values must be unique" in str(exc.value)


def test_single_column_dcid_only_raises():
    # Only the 'dcid' column, even with rows
    df = pd.DataFrame({"dcid": ["a", "b"]})
    with pytest.raises(ValueError) as exc:
        concordance.validate_concordance_table(df)
    assert "at least 2 columns" in str(exc.value)


def test_valid_concordance_table_passes():
    # 'dcid' plus at least one other column, with no nulls or duplicates
    df = pd.DataFrame({
        "dcid": ["id1", "id2", "id3"],
        "name": ["A", "B", "C"],
        "extra": [10, 20, 30],
    })
    # Should not raise
    assert concordance.validate_concordance_table(df) is None


# ——————————————————————————————————————————————————————————————————————————
# get_concordance_dict tests
# ——————————————————————————————————————————————————————————————————————————

@pytest.fixture(scope="module")
def master_concordance_df():
    """Fixture for a sample concordance DataFrame with various columns."""

    return pd.DataFrame({
        "dcid": ["country/ZWE", "country/ITA", "country/FRA", "nuts/FI2", "country/CPV"],
        "name_official": ['Zimbabwe', 'Italy', 'France', 'Åland Islands', 'Cabo Verde'],
        "iso3_code": ['ZWE', 'ITA', 'FRA', 'ALA', 'CPV'],
        "income_level": ['Lower middle income', 'High income', 'High income', None, 'Lower middle income']
    })


def test_get_concordance_dict_identity_mapping(master_concordance_df):
    """When from_type == to_type, each dcid should map to itself,with the key cleaned via clean_string."""
    result = concordance.get_concordance_dict(
        master_concordance_df, "dcid", "dcid"
    )

    expected = {
        "countryzwe": "country/ZWE",
        "countryita": "country/ITA",
        "countryfra": "country/FRA",
        "nutsfi2":    "nuts/FI2",
        "countrycpv": "country/CPV",
    }
    assert result == expected

def test_get_concordance_dict_cross_mapping_name_official_to_dcid(master_concordance_df):
    """When from_type != to_type, should map cleaned name_official → dcid, dropping any rows where dcid is null (none here)."""
    result = concordance.get_concordance_dict(
        master_concordance_df,
        from_type="name_official",
        to_type="dcid",
    )

    expected = {
        "zimbabwe":       "country/ZWE",
        "italy":          "country/ITA",
        "france":         "country/FRA",
        "alandislands":   "nuts/FI2",
        "caboverde":      "country/CPV",
    }
    assert result == expected


def test_get_concordance_dict_cross_mapping_iso3_code_to_dcid(master_concordance_df):
    """Cross‐column mapping for iso3_code → dcid, cleaning the ISO codes to lower‐case keys."""
    result = concordance.get_concordance_dict(
        master_concordance_df,
        from_type="iso3_code",
        to_type="dcid",
    )

    expected = {
        "zwe": "country/ZWE",
        "ita": "country/ITA",
        "fra": "country/FRA",
        "ala": "nuts/FI2",
        "cpv": "country/CPV",
    }
    assert result == expected

def test_get_concordance_dict_income_level_drops_nulls(master_concordance_df):
    """
    Mapping from `iso3_code` → `income_level` should drop any rows
    where `income_level` is null (i.e. 'ALA').
    """
    result = concordance.get_concordance_dict(
        master_concordance_df,
        from_type="iso3_code",
        to_type="income_level",
    )

    expected = {
        "zwe": "Lower middle income",
        "ita": "High income",
        "fra": "High income",
        "cpv": "Lower middle income",
    }
    assert result == expected


# ——————————————————————————————————————————————————————————————————————————
# _map_single_or_list tests
# ——————————————————————————————————————————————————————————————————————————

@pytest.fixture(scope="module")
def iso_to_dcid(master_concordance_df):
    # reuse the same concordance fixture to build a simple lookup
    return concordance.get_concordance_dict(
        master_concordance_df, from_type="iso3_code", to_type="dcid"
    )

def test_map_single_or_list_multiple_hits(iso_to_dcid):
    """Given a list of values, _map_single_or_list should:
    - clean each entry,
    - look it up in the concordance dict,
    - drop any misses,
    - and return a list of all matched values.
    """
    # mix of hits and one miss
    vals = ["ZWE", "XXX", "CPV"]
    result = concordance._map_single_or_list(vals, iso_to_dcid)

    # "ZWE" -> "country/ZWE", "XXX" dropped, "CPV" -> "country/CPV"
    assert isinstance(result, list)
    assert result == ["country/ZWE", "country/CPV"]


def test_map_single_or_list_scalar_miss(iso_to_dcid):
    """A scalar value not in the dict should return None."""
    assert concordance._map_single_or_list("XYZ", iso_to_dcid) is None

def test_map_single_or_list_all_misses(iso_to_dcid):
    """A list where none of the cleaned keys match should return None."""
    assert concordance._map_single_or_list(["AAA", "BBB"], iso_to_dcid) is None

def test_map_single_or_list_single_hit(iso_to_dcid):
    """If exactly one entry in the list matches, return that single value."""
    vals = ["XXX", "ITA", "YYY"]  # only "ITA" is in the dict
    assert concordance._map_single_or_list(vals, iso_to_dcid) == "country/ITA"

def test_map_single_or_list_empty_list(iso_to_dcid):
    """An empty list should return None."""
    assert concordance._map_single_or_list([], iso_to_dcid) is None
