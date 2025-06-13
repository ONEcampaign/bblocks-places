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

def test_identity_map_same_from_and_to():
    """Test that when from_type and to_type are the same, it returns a mapping of cleaned values to original values."""
    df = pd.DataFrame({
        "foo": ["A B", "C-D", None, "   E_f!"],
    })
    result = concordance.get_concordance_dict(df, "foo", "foo")
    # clean_string("A B") -> "ab", "C-D" -> "cd", "   E_f!" -> "ef"
    assert result == {
        "ab": "A B",
        "cd": "C-D",
        "ef": "   E_f!",
    }


# def test_cross_column_mapping_drops_nulls_and_cleans_keys():
#     df = pd.DataFrame({
#         "country": ["Côte d'Ivoire", " Foo Bar ", None],
#         "dcid":    ["country/CI",         None,         "country/XX"],
#     })
#     result = concordance.get_concordance_dict(df, "country", "dcid")
#     # Only the first row survives; clean_string("Côte d'Ivoire") -> "cotedivoire"
#     assert result == {
#         "cotedivoire": "country/CI"
#     }
#
#
# def test_missing_from_or_to_column_raises_keyerror():
#     df = pd.DataFrame({
#         "a": [1, 2],
#         "b": [3, 4],
#     })
#     with pytest.raises(KeyError):
#         concordance.get_concordance_dict(df, "nonexistent", "a")
#     with pytest.raises(KeyError):
#         concordance.get_concordance_dict(df, "a", "nonexistent")
#
#
# def test_duplicate_cleaned_keys_last_one_wins():
#     df = pd.DataFrame({
#         "code": ["X", " x ", "Y"],
#         "dcid": ["id1", "id2", "id3"],
#     })
#     result = concordance.get_concordance_dict(df, "code", "dcid")
#     # "X" and " x " both clean to "x", so the second ("id2") should overwrite the first
#     assert result == {
#         "x": "id2",
#         "y": "id3",
#     }
#
#
# def test_all_null_to_column_yields_empty_dict():
#     df = pd.DataFrame({
#         "from": ["a", "b", "c"],
#         "to":   [None, None, None],
#     })
#     result = concordance.get_concordance_dict(df, "from", "to")
#     assert result == {}

