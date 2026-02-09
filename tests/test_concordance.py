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
    df = pd.DataFrame(
        {
            "dcid": ["a", None, "c"],
            "other": [1, 2, 3],
        }
    )
    with pytest.raises(ValueError) as exc:
        concordance.validate_concordance_table(df)
    assert "must not contain null values" in str(exc.value)


def test_duplicate_dcid_values_raises():
    df = pd.DataFrame(
        {
            "dcid": ["x", "x", "y"],
            "other": [1, 2, 3],
        }
    )
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
    df = pd.DataFrame(
        {
            "dcid": ["id1", "id2", "id3"],
            "name": ["A", "B", "C"],
            "extra": [10, 20, 30],
        }
    )
    # Should not raise
    assert concordance.validate_concordance_table(df) is None


# ——————————————————————————————————————————————————————————————————————————
# get_concordance_dict tests
# ——————————————————————————————————————————————————————————————————————————


@pytest.fixture(scope="module")
def master_concordance_df():
    """Fixture for a sample concordance DataFrame with various columns."""

    return pd.DataFrame(
        {
            "dcid": [
                "country/ZWE",
                "country/ITA",
                "country/FRA",
                "nuts/FI2",
                "country/CPV",
            ],
            "name_official": [
                "Zimbabwe",
                "Italy",
                "France",
                "Åland Islands",
                "Cabo Verde",
            ],
            "iso3_code": ["ZWE", "ITA", "FRA", "ALA", "CPV"],
            "income_level": [
                "Lower middle income",
                "High income",
                "High income",
                None,
                "Lower middle income",
            ],
        }
    )


def test_get_concordance_dict_identity_mapping(master_concordance_df):
    """When from_type == to_type, each dcid should map to itself,with the key cleaned via clean_string."""
    result = concordance.get_concordance_dict(master_concordance_df, "dcid", "dcid")

    expected = {
        "countryzwe": "country/ZWE",
        "countryita": "country/ITA",
        "countryfra": "country/FRA",
        "nutsfi2": "nuts/FI2",
        "countrycpv": "country/CPV",
    }
    assert result == expected


def test_get_concordance_dict_cross_mapping_name_official_to_dcid(
    master_concordance_df,
):
    """When from_type != to_type, should map cleaned name_official → dcid, dropping any rows where dcid is null (none here)."""
    result = concordance.get_concordance_dict(
        master_concordance_df,
        from_type="name_official",
        to_type="dcid",
    )

    expected = {
        "zimbabwe": "country/ZWE",
        "italy": "country/ITA",
        "france": "country/FRA",
        "alandislands": "nuts/FI2",
        "caboverde": "country/CPV",
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
# get_concordance_dict tests with numeric from_type
# ——————————————————————————————————————————————————————————————————————————


@pytest.fixture(scope="module")
def numeric_concordance_df():
    """Fixture for a concordance DataFrame with a numeric column (like dac_code)."""
    return pd.DataFrame(
        {
            "dcid": ["country/FRA", "country/AFG", "country/ZWE"],
            "name_short": ["France", "Afghanistan", "Zimbabwe"],
            "dac_code": pd.array([4, 625, 71], dtype="Int64"),
        }
    )


def test_get_concordance_dict_numeric_from_type(numeric_concordance_df):
    """Numeric from_type keys should be converted to strings via clean_string."""
    result = concordance.get_concordance_dict(
        numeric_concordance_df, from_type="dac_code", to_type="dcid"
    )
    assert result == {
        "4": "country/FRA",
        "625": "country/AFG",
        "71": "country/ZWE",
    }


def test_get_concordance_dict_numeric_to_type(numeric_concordance_df):
    """Numeric to_type values should preserve their original type."""
    result = concordance.get_concordance_dict(
        numeric_concordance_df, from_type="name_short", to_type="dac_code"
    )
    # Values should remain as integers
    assert result["france"] == 4
    assert result["afghanistan"] == 625
    assert result["zimbabwe"] == 71


def test_get_concordance_dict_numeric_identity(numeric_concordance_df):
    """Identity mapping on a numeric column should work and preserve original values."""
    result = concordance.get_concordance_dict(
        numeric_concordance_df, from_type="dac_code", to_type="dac_code"
    )
    # Keys are cleaned strings, values are original integers
    assert result["4"] == 4
    assert result["625"] == 625
    assert result["71"] == 71


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


def test_map_single_or_list_numeric_scalar(numeric_concordance_df):
    """A numeric scalar should be found in a concordance dict keyed by numeric from_type."""
    conc_dict = concordance.get_concordance_dict(
        numeric_concordance_df, from_type="dac_code", to_type="dcid"
    )
    assert concordance._map_single_or_list(4, conc_dict) == "country/FRA"


def test_map_single_or_list_numeric_list(numeric_concordance_df):
    """A list of numeric values should be resolved correctly."""
    conc_dict = concordance.get_concordance_dict(
        numeric_concordance_df, from_type="dac_code", to_type="dcid"
    )
    result = concordance._map_single_or_list([4, 625], conc_dict)
    assert isinstance(result, list)
    assert set(result) == {"country/FRA", "country/AFG"}


def test_map_single_or_list_numeric_miss(numeric_concordance_df):
    """A numeric value not in the dict should return None."""
    conc_dict = concordance.get_concordance_dict(
        numeric_concordance_df, from_type="dac_code", to_type="dcid"
    )
    assert concordance._map_single_or_list(9999, conc_dict) is None


# —————————————————————————————————————————————————————————————————————————
# map_places tests
# —————————————————————————————————————————————————————————————————————————


def test_map_places_basic_hits(master_concordance_df):
    """Basic success case: every place in the list maps to a single dcid."""
    places = ["Zimbabwe", "Italy", "France"]
    result = concordance.map_places(
        master_concordance_df,
        places,
        from_type="name_official",
        to_type="dcid",
    )
    assert result == {
        "Zimbabwe": "country/ZWE",
        "Italy": "country/ITA",
        "France": "country/FRA",
    }


def test_map_places_numeric_from_type(numeric_concordance_df):
    """map_places should work when places are numeric values (e.g. dac_code)."""
    result = concordance.map_places(
        numeric_concordance_df,
        [4, 625],
        from_type="dac_code",
        to_type="name_short",
    )
    assert result == {4: "France", 625: "Afghanistan"}


def test_map_places_numeric_to_type(numeric_concordance_df):
    """map_places should preserve numeric values when to_type is numeric."""
    result = concordance.map_places(
        numeric_concordance_df,
        ["France", "Zimbabwe"],
        from_type="name_short",
        to_type="dac_code",
    )
    assert result == {"France": 4, "Zimbabwe": 71}


def test_map_candidates_none_candidate_stays_none(master_concordance_df):
    """
    A None candidate value should remain None in the output.
    """
    candidates = {"Atlantis": None}
    result = concordance.map_candidates(
        master_concordance_df,
        candidates,
        "iso3_code",  # mapping DCID → iso3_code
    )
    assert result == {"Atlantis": None}


def test_map_candidates_single_string_hit(master_concordance_df):
    """
    A single‐string candidate that matches a DCID should map to its iso3_code.
    """
    candidates = {"Zimbabwe": "country/ZWE"}
    result = concordance.map_candidates(
        master_concordance_df,
        candidates,
        "iso3_code",
    )
    assert result == {"Zimbabwe": "ZWE"}


def test_map_candidates_single_string_miss(master_concordance_df):
    """
    A single‐string candidate not found in the concordance should map to None.
    """
    candidates = {"Unknown": "country/XXX"}
    result = concordance.map_candidates(
        master_concordance_df,
        candidates,
        "iso3_code",
    )
    assert result == {"Unknown": None}


def test_map_candidates_list_single_hit(master_concordance_df):
    """
    A list candidate with exactly one hit (others miss) should return that single value.
    """
    candidates = {"Mix": ["country/ITA", "country/XXX"]}
    result = concordance.map_candidates(
        master_concordance_df,
        candidates,
        "iso3_code",
    )
    assert result == {"Mix": "ITA"}


def test_map_candidates_list_multiple_hits(master_concordance_df):
    """
    A list candidate with multiple hits should return a list of matched values.
    """
    candidates = {"Union": ["country/ZWE", "country/FRA", "country/XXX"]}
    result = concordance.map_candidates(
        master_concordance_df,
        candidates,
        "iso3_code",
    )
    assert isinstance(result["Union"], list)
    assert set(result["Union"]) == {"ZWE", "FRA"}


def test_map_candidates_list_all_misses(master_concordance_df):
    """
    A list candidate where none match should return None.
    """
    candidates = {"Nothing": ["country/XXX", "country/YYY"]}
    result = concordance.map_candidates(
        master_concordance_df,
        candidates,
        "iso3_code",
    )
    assert result == {"Nothing": None}


def test_map_candidates_empty_input(master_concordance_df):
    """
    An empty candidates dict should return an empty dict.
    """
    result = concordance.map_candidates(
        master_concordance_df,
        {},
        "iso3_code",
    )
    assert result == {}


# —————————————————————————————————————————————————————————————————————————
# fetch_properties tests
# —————————————————————————————————————————————————————————————————————————

# Mocking DataCommonsClient and related classes for tests


class FakeNode:
    """Simulates the DataCommons Node object with value and name attributes."""

    def __init__(self, value=None, name=None):
        self.value = value
        self.name = name


class FakeResponse:
    """Simulates the response from fetch_property_values()."""

    def __init__(self, properties):
        # properties: dict[str, FakeNode or list[FakeNode]]
        self._properties = properties

    def get_properties(self):
        return self._properties


class FakeNodeClient:
    """Simulates the `client.node` interface."""

    def __init__(self, response_map):
        """
        response_map: dict[tuple(dcids, property), dict[str, FakeNode | list[FakeNode]]]
        """
        self._response_map = response_map

    def fetch_property_values(self, dcids, dc_property):
        # Use the tuple of dcids and property name to find the fake response
        key = (tuple(dcids), dc_property)
        properties = self._response_map.get(key, {})
        return FakeResponse(properties)


class FakeDCClient:
    """Simulates the DataCommonsClient for use in fetch_properties tests."""

    def __init__(self, response_map):
        # The .node attribute provides fetch_property_values(...)
        self.node = FakeNodeClient(response_map)


def test_fetch_properties_empty_input():
    """
    If dcids list is empty, fetch_properties should return an empty dict.
    """
    fake_client = FakeDCClient(response_map={})
    result = concordance.fetch_properties(fake_client, [], "population")
    assert result == {}


def test_fetch_properties_single_node_value():
    """
    Single‐node response with a non‐null .value should return that value.
    """
    response_map = {
        (("ID1",), "population"): {"ID1": FakeNode(value="1000", name=None)}
    }
    fake_client = FakeDCClient(response_map)
    result = concordance.fetch_properties(fake_client, ["ID1"], "population")
    assert result == {"ID1": "1000"}


def test_fetch_properties_single_node_name_fallback():
    """
    Single‐node response with .value None but .name present should return .name.
    """
    response_map = {(("ID2",), "prop"): {"ID2": FakeNode(value=None, name="Name2")}}
    fake_client = FakeDCClient(response_map)
    result = concordance.fetch_properties(fake_client, ["ID2"], "prop")
    assert result == {"ID2": "Name2"}


def test_fetch_properties_multi_node_mixed():
    """
    Multi‐node response mixing value and name should return a list of both.
    """
    response_map = {
        (("ID3",), "prop"): {
            "ID3": [FakeNode(value="A", name=None), FakeNode(value=None, name="B")]
        }
    }
    fake_client = FakeDCClient(response_map)
    result = concordance.fetch_properties(fake_client, ["ID3"], "prop")
    assert isinstance(result["ID3"], list)
    assert result["ID3"] == ["A", "B"]


def test_fetch_properties_multi_node_all_null():
    """
    Multi‐node response where all nodes have neither value nor name should yield None.
    """
    response_map = {(("ID4",), "prop"): {"ID4": [FakeNode(value=None, name=None)]}}
    fake_client = FakeDCClient(response_map)
    result = concordance.fetch_properties(fake_client, ["ID4"], "prop")
    assert result == {"ID4": None}


def test_fetch_properties_mixed_dcids():
    """
    Mixed-case: one with .value, one with name fallback, one list, one all-null.
    """
    response_map = {
        (("A", "B", "C", "D"), "prop"): {
            "A": FakeNode(value="ValA", name=None),
            "B": FakeNode(value=None, name="NameB"),
            "C": [FakeNode(value="C1", name=None), FakeNode(value=None, name="C2")],
            "D": [FakeNode(value=None, name=None)],
        }
    }
    fake_client = FakeDCClient(response_map)
    result = concordance.fetch_properties(fake_client, ["A", "B", "C", "D"], "prop")
    assert result == {"A": "ValA", "B": "NameB", "C": ["C1", "C2"], "D": None}
