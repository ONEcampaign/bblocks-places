"""Tests for the resolver module."""

import pytest
import pandas as pd
import logging

from bblocks.places import resolver
from bblocks.places.resolver import PlaceResolver
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


# ----------------------------------------
# Tests for the PlaceResolver class
# ----------------------------------------


# Tests for __init__ method
def test_init_with_no_concordance_table():
    """concordance_table=None should set _concordance_table to None."""
    pr = PlaceResolver(concordance_table=None)
    assert pr._concordance_table is None


def test_init_with_default_concordance_table(monkeypatch):
    """concordance_table='default' should load class _CONCORDANCE_TABLE and validate it."""
    dummy_df = pd.DataFrame({"dcid": ["X"], "foo": ["bar"]})
    called = {}

    # stub out the class‐level table and the validator
    monkeypatch.setattr(resolver.PlaceResolver, "_CONCORDANCE_TABLE", dummy_df)
    monkeypatch.setattr(resolver, "validate_concordance_table",
                        lambda df: called.setdefault("validated", df))

    pr = PlaceResolver(concordance_table="default")
    # it should pick up our dummy_df
    assert pr._concordance_table is dummy_df
    # and call validate_concordance_table exactly once with dummy_df
    assert called["validated"] is dummy_df


def test_init_with_invalid_concordance_string():
    """concordance_table=<bad string> should raise ValueError."""
    with pytest.raises(ValueError):
        PlaceResolver(concordance_table="not_default")


def test_init_with_custom_disambiguation_default():
    """custom_disambiguation='default' should load resolver._EDGE_CASES."""
    pr = PlaceResolver(concordance_table=None, custom_disambiguation="default")
    assert pr._custom_disambiguation is resolver.PlaceResolver._EDGE_CASES


def test_init_with_custom_disambiguation_dict():
    """custom_disambiguation=dict should set _custom_disambiguation to that dict."""
    custom = {"foo": "X"}
    pr = PlaceResolver(concordance_table=None, custom_disambiguation=custom)
    assert pr._custom_disambiguation == custom


def test_init_with_dc_api_settings(monkeypatch):
    """Providing dc_api_settings should pass them into DataCommonsClient."""
    settings = {"api_key": "KEY", "url": "https://example.com"}
    captured = {}

    class DummyDC:
        def __init__(self, **kwargs):
            captured.update(kwargs)
    monkeypatch.setattr(resolver, "DataCommonsClient", DummyDC)

    pr = PlaceResolver(concordance_table=None, dc_api_settings=settings)
    # Should have created self._dc_client via DummyDC with our settings
    assert isinstance(pr._dc_client, DummyDC)
    assert captured == settings


# -------------------------------------------------
# Tests for from_concordance_csv method
# -------------------------------------------------

def test_from_concordance_csv_reads_csv_and_sets_table(monkeypatch, tmp_path):
    """from_concordance_csv() should call pd.read_csv on the given path and use that DataFrame."""
    dummy_df = pd.DataFrame({"dcid": ["X"], "foo": ["bar"]})
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("dummy")  # the content is irrelevant

    called = {}
    def fake_read_csv(path, *args, **kwargs):
        # Assert the path passed is exactly our csv_path
        assert str(path) == str(csv_path)
        called["read"] = True
        return dummy_df

    monkeypatch.setattr(resolver.pd, "read_csv", fake_read_csv)

    pr = PlaceResolver.from_concordance_csv(csv_path, custom_disambiguation={"A": "a"}, dc_entity_type="Country")

    # Ensure pd.read_csv was invoked
    assert called.get("read", False), "pd.read_csv was not called"
    # The new resolver should have our dummy dataframe as its concordance table
    assert pr._concordance_table is dummy_df
    # Extra args/kwargs should be forwarded to the constructor
    assert pr._custom_disambiguation == {"A": "a"}
    assert pr._dc_entity_type == "Country"


# -------------------------------------------------
# Tests for the concordance_table property
# -------------------------------------------------

def test_concordance_table_property_returns_df():
    """Returns the stored DataFrame when one is set."""
    dummy = pd.DataFrame({"dcid": ["X"], "foo": ["bar"]})
    pr = PlaceResolver(concordance_table=None)
    # manually inject
    pr._concordance_table = dummy
    assert pr.concordance_table is dummy

def test_concordance_table_property_raises_when_none():
    """Raises ValueError if no concordance table is defined."""
    pr = PlaceResolver(concordance_table=None)
    pr._concordance_table = None
    with pytest.raises(ValueError):
        _ = pr.concordance_table


# -------------------------------------------------
# Tests for add_custom_disambiguation method
# -------------------------------------------------

def test_add_custom_disambiguation_sets_new_dict():
    """Sets _custom_disambiguation when it was None and returns self."""
    pr = PlaceResolver(concordance_table=None, custom_disambiguation=None)
    # Simulate starting with no custom rules
    pr._custom_disambiguation = None

    custom = {"X": "dc/X"}
    returned = pr.add_custom_disambiguation(custom)

    assert returned is pr
    assert pr._custom_disambiguation == {"X": "dc/X"}

def test_add_custom_disambiguation_updates_existing_dict():
    """Merges new rules into existing _custom_disambiguation and returns self."""
    initial = {"A": "dc/A"}
    pr = PlaceResolver(concordance_table=None, custom_disambiguation=initial.copy())

    new_rules = {"B": "dc/B"}
    returned = pr.add_custom_disambiguation(new_rules)

    assert returned is pr
    # Original entry plus the new one
    assert pr._custom_disambiguation == {"A": "dc/A", "B": "dc/B"}


# -------------------------------------------------
# Test resolve_map method
# -------------------------------------------------

def test_resolve_map_basic_concordance_mapping():
    """Basic mapping: resolve_map uses concordance_table when to_type exists."""
    # build a tiny concordance table
    df = pd.DataFrame({
        "dcid": ["dc/1", "dc/2"],
        "name": ["Alpha", "Beta"],
        "region": ["RegA", "RegB"]
    })
    pr = PlaceResolver(concordance_table=df)
    # map names → regions
    result = pr.resolve_map(["Alpha", "Beta"], from_type="name", to_type="region")
    assert result == {"Alpha": "RegA", "Beta": "RegB"}

def test_resolve_map_not_found_ignore_returns_none():
    """When a place isn’t in the concordance and not_found='ignore', it yields None."""
    df = pd.DataFrame({
        "dcid": ["dc/1"],
        "name": ["Alpha"],
        "region": ["RegA"]
    })
    pr = PlaceResolver(concordance_table=df)
    result = pr.resolve_map(["Gamma"], from_type="name", to_type="region", not_found="ignore")
    assert result == {"Gamma": None}

def test_resolve_map_custom_mapping_overrides_concordance():
    """custom_mapping keys bypass concordance entirely."""
    df = pd.DataFrame({
        "dcid": ["dc/1", "dc/2"],
        "name": ["X", "Y"],
        "region": ["OldX", "OldY"]
    })
    # even though concordance says X→OldX, custom_mapping should win
    custom = {"X": "NewX"}
    pr = PlaceResolver(concordance_table=df)
    result = pr.resolve_map(["X", "Y"], from_type="name", to_type="region", custom_mapping=custom)
    assert result == {"X": "NewX", "Y": "OldY"}


# -------------------------------------------------
# Test resolve method
# -------------------------------------------------

def test_resolve_string_to_scalar():
    """A single place string returns its mapped scalar value."""
    df = pd.DataFrame({
        "dcid": ["c/1"],
        "name": ["Alpha"],
        "region": ["RegA"]
    })
    pr = PlaceResolver(concordance_table=df)
    assert pr.resolve("Alpha", from_type="name", to_type="region") == "RegA"

def test_resolve_list_to_list_with_ignore():
    """A list of places returns a list, with None for missing when not_found='ignore'."""
    df = pd.DataFrame({
        "dcid": ["c/1"],
        "name": ["Alpha"],
        "region": ["RegA"]
    })
    pr = PlaceResolver(concordance_table=df)
    result = pr.resolve(
        ["Alpha", "Gamma"],
        from_type="name",
        to_type="region",
        not_found="ignore"
    )
    assert result == ["RegA", None]

def test_resolve_series_preserves_index_and_type():
    """Pandas Series input returns a Series with identical index and corresponding values."""
    df = pd.DataFrame({
        "dcid": ["c/1"],
        "name": ["Alpha"],
        "region": ["RegA"]
    })
    pr = PlaceResolver(concordance_table=df)
    series_in = pd.Series(["Alpha", "Gamma"], index=["i", "j"])
    series_out = pr.resolve(
        series_in,
        from_type="name",
        to_type="region",
        not_found="ignore"
    )
    assert isinstance(series_out, pd.Series)
    assert list(series_out.index) == ["i", "j"]
    assert list(series_out.values) == ["RegA", None]

def test_resolve_missing_raises_and_ignore_nulls_bypasses():
    """not_found='raise' triggers PlaceNotFoundError; ignore_nulls=True with not_found='ignore' yields None."""
    df = pd.DataFrame({
        "dcid": ["c/1"],
        "name": ["Alpha"],
        "region": ["RegA"]
    })
    pr = PlaceResolver(concordance_table=df)

    # missing with not_found='raise'
    with pytest.raises(PlaceNotFoundError):
        pr.resolve("Gamma", from_type="name", to_type="region", not_found="raise")

    # missing but ignore_nulls=True and not_found='ignore'
    result = pr.resolve(
        "Gamma",
        from_type="name",
        to_type="region",
        not_found="ignore",
        ignore_nulls=True
    )
    assert result is None

def test_resolve_custom_mapping_overrides_concordance():
    """Custom mapping entry takes precedence over concordance_table."""
    df = pd.DataFrame({
        "dcid": ["c/X", "c/Y"],
        "name": ["X", "Y"],
        "region": ["OldX", "OldY"]
    })
    custom_map = {"X": "NewX"}
    pr = PlaceResolver(concordance_table=df)

    # X should use custom_map, Y falls back to concordance
    assert pr.resolve(
        "X",
        from_type="name",
        to_type="region",
        custom_mapping=custom_map
    ) == "NewX"
    assert pr.resolve(
        "Y",
        from_type="name",
        to_type="region",
        custom_mapping=custom_map
    ) == "OldY"


# -------------------------------------------------
# Tests for the filter method
# -------------------------------------------------

def test_filter_list_basic_region():
    """Filtering a list of names by a single region returns only matching names."""
    df = pd.DataFrame({
        "dcid": ["c1", "c2", "c3"],
        "name": ["A", "B", "C"],
        "region": ["R1", "R2", "R1"]
    })
    pr = PlaceResolver(concordance_table=df)
    result = pr.filter(
        ["A", "B", "C"],
        filters={"region": "R1"},
        from_type="name"
    )
    assert result == ["A", "C"]

def test_filter_list_multiple_criteria():
    """Applying multiple filters in sequence yields the intersection of matches."""
    df = pd.DataFrame({
        "dcid": ["c1", "c2", "c3", "c4"],
        "name": ["A", "B", "C", "D"],
        "region": ["R1", "R2", "R1", "R2"],
        "group": ["G1", "G1", "G2", "G2"]
    })
    pr = PlaceResolver(concordance_table=df)
    result = pr.filter(
        ["A", "B", "C", "D"],
        filters={"region": ["R1"], "group": "G2"},
        from_type="name"
    )
    assert result == ["C"]

def test_filter_series_returns_series_of_matching_values():
    """Filtering a pandas Series returns a new Series containing only matching entries."""
    df = pd.DataFrame({
        "dcid": ["c1", "c2", "c3"],
        "name": ["A", "B", "C"],
        "region": ["R1", "R2", "R1"]
    })
    pr = PlaceResolver(concordance_table=df)
    series_in = pd.Series(["A", "B", "C", "A"])
    series_out = pr.filter(
        series_in,
        filters={"region": "R1"},
        from_type="name"
    )
    assert isinstance(series_out, pd.Series)
    # Should include only A, C, A in original order
    assert list(series_out.values) == ["A", "C", "A"]

def test_filter_invalid_places_type_raises():
    """Passing a non-list, non-Series as places raises ValueError."""
    df = pd.DataFrame({
        "dcid": ["c1"],
        "name": ["A"],
        "region": ["R1"]
    })
    pr = PlaceResolver(concordance_table=df)
    with pytest.raises(ValueError):
        pr.filter(("A", "B"), filters={"region": "R1"}, from_type="name")

def test_filter_unknown_category_raises_keyerror():
    """Filtering by a category not in concordance table raises KeyError."""
    df = pd.DataFrame({
        "dcid": ["c1"],
        "name": ["A"],
        "region": ["R1"]
    })
    pr = PlaceResolver(concordance_table=df)
    with pytest.raises(KeyError):
        pr.filter(["A"], filters={"unknown_category": "X"}, from_type="name")


# -------------------------------------------------
# Tests for the get_concordance_dict method
# -------------------------------------------------

def test_get_concordance_dict_error_on_no_table():
    """Raises ValueError if the resolver has no concordance table defined."""
    df = pd.DataFrame({
        "dcid": ["c1"],
        "name": ["A"],
        "region": ["R1"]
    })
    pr = PlaceResolver(concordance_table=df)
    # simulate missing table
    pr._concordance_table = None
    with pytest.raises(ValueError) as exc:
        pr.get_concordance_dict("name", "region")
    assert "No concordance table is defined" in str(exc.value)

def test_get_concordance_dict_same_column_logs_warning_and_identity(caplog):
    """When from_type == to_type, returns identity mapping and logs a warning."""
    df = pd.DataFrame({
        "dcid": ["c1", "c2", "c3"],
        "name": ["A", "B", "C"],
        "region": ["R1", "R2", "R3"]
    })
    pr = PlaceResolver(concordance_table=df)

    caplog.set_level(logging.WARNING, logger="bblocks.places.resolver")
    mapping = pr.get_concordance_dict("name", "name")

    # mapping should be identity on the 'name' column
    expected = {"A": "A", "B": "B", "C": "C"}
    assert mapping == expected

    # and we should have logged exactly that warning
    logs = [r.getMessage() for r in caplog.records]
    assert any("from_type and to_type are the same" in msg for msg in logs)

def test_get_concordance_dict_drops_nulls_by_default():
    """By default (include_nulls=False), entries with null target values are removed."""
    df = pd.DataFrame({
        "dcid": ["c1", "c2", "c3"],
        "name": ["A", "B", "C"],
        "region": ["X", None, "Z"]
    })
    pr = PlaceResolver(concordance_table=df)
    mapping = pr.get_concordance_dict("name", "region")
    # "B" had a null region, so it should be dropped
    assert mapping == {"A": "X", "C": "Z"}

def test_get_concordance_dict_include_nulls_returns_none():
    """With include_nulls=True, nulls are kept and represented as None."""
    df = pd.DataFrame({
        "dcid": ["c1", "c2", "c3"],
        "name": ["A", "B", "C"],
        "region": ["X", None, "Z"]
    })
    pr = PlaceResolver(concordance_table=df)
    mapping = pr.get_concordance_dict("name", "region", include_nulls=True)
    # "B" should map explicitly to None
    assert mapping == {"A": "X", "B": None, "C": "Z"}