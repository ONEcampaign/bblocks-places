"""Tests for the main module."""

import pytest
import pandas as pd
import logging

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


# ----------------------------------------------
# Tests for boolean getters
# ----------------------------------------------


# Only the getters that go through _get_list_from_bool
BOOLEAN_GETTERS = [
    (main.get_un_members, "un_member"),
    (main.get_un_observers, "un_observer"),
    (main.get_m49_places, "m49_member"),
    (main.get_sids, "sids"),
    (main.get_ldc, "ldc"),
    (main.get_lldc, "lldc"),
]

@pytest.mark.parametrize("func,bool_field", BOOLEAN_GETTERS)
def test_boolean_getter_returns_only_true(monkeypatch, func, bool_field):
    """Each getter should return only the keys with True values."""
    sample = {"A": True, "B": False, "C": True}
    # stub get_concordance_dict on the resolver
    monkeypatch.setattr(
        main._country_resolver,
        "get_concordance_dict",
        lambda from_type, to_type: sample
    )
    out = func(place_format="dcid")
    assert out == ["A", "C"]

@pytest.mark.parametrize("func,bool_field", BOOLEAN_GETTERS)
def test_boolean_getter_empty_returns_empty_list(monkeypatch, caplog, func, bool_field):
    """When no entries are True, each getter returns [] and logs a warning by default."""
    monkeypatch.setattr(
        main._country_resolver,
        "get_concordance_dict",
        lambda from_type, to_type: {"X": False}
    )
    caplog.set_level("WARNING")
    out = func(place_format="dcid")
    assert out == []
    assert f"No places found for boolean field '{bool_field}'" in caplog.text

@pytest.mark.parametrize("func,bool_field", BOOLEAN_GETTERS)
def test_boolean_getter_empty_raise_if_empty(monkeypatch, func, bool_field):
    """When no entries are True and raise_if_empty=True, each getter should raise ValueError."""
    monkeypatch.setattr(
        main._country_resolver,
        "get_concordance_dict",
        lambda from_type, to_type: {"X": False}
    )
    with pytest.raises(ValueError) as exc:
        func(place_format="dcid", raise_if_empty=True)
    assert f"No places found for boolean field '{bool_field}'" in str(exc.value)

def test_boolean_getter_invalid_format_raises():
    """Passing an invalid place_format raises before fetching anything."""
    with pytest.raises(ValueError):
        main.get_un_members(place_format="not_a_format")

# --------------------------------------------------
# get_african_countries uses get_places → test separately
# --------------------------------------------------

def test_get_african_countries_delegates_to_get_places(monkeypatch):
    """get_african_countries should simply call get_places with region='Africa' (+ un_member)."""
    called = {}
    def fake_get_places(filters, place_format, raise_if_empty=False):
        called['filters'] = filters
        called['fmt'] = place_format
        called['raise'] = raise_if_empty
        return ["X", "Y"]
    monkeypatch.setattr(main, "get_places", fake_get_places)

    out = main.get_african_countries(place_format="name_official", exclude_non_un_members=True)
    assert out == ["X", "Y"]
    assert called['filters'] == {"region": "Africa", "un_member": True}
    assert called['fmt'] == "name_official"
    assert called['raise'] is False

def test_get_african_countries_without_excluding_non_un(monkeypatch):
    """exclude_non_un_members=False should not include the un_member filter."""
    called = {}
    monkeypatch.setattr(main, "get_places", lambda filters, place_format, raise_if_empty=False: [])
    # run with exclude_non_un_members=False
    main.get_african_countries(place_format="dcid", exclude_non_un_members=False, raise_if_empty=False)
    # filters should only be region=Africa
    # (we can't inspect inside lambda, so do a real fake)
    def track(filters, place_format, raise_if_empty=False):
        called['filters'] = filters
    monkeypatch.setattr(main, "get_places", track)
    main.get_african_countries(exclude_non_un_members=False)
    assert called['filters'] == {"region": "Africa"}

def test_get_african_countries_raise_if_empty(monkeypatch):
    """get_african_countries should propagate raise_if_empty to get_places."""
    def fake_get_places(filters, place_format, raise_if_empty=False):
        raise ValueError("boom")
    monkeypatch.setattr(main, "get_places", fake_get_places)
    with pytest.raises(ValueError):
        main.get_african_countries(raise_if_empty=True)


#  --------------------------------------------------
# Tests for get_places
#  --------------------------------------------------

def test_get_places_basic_filter(monkeypatch):
    """get_places returns matching values from the concordance_table."""
    df = pd.DataFrame({
        'dcid': ['c1', 'c2', 'c3', 'c4'],
        'name_official': ['A', 'B', 'C', 'D'],
        'region': ['R1', 'R2', 'R1', 'R3'],
        'income_level': ['High', 'Low', 'High', 'Low']
    })
    monkeypatch.setattr(main._country_resolver, '_concordance_table', df)

    result = main.get_places(
        filters={'region': 'R1'},
        place_format='name_official',
        raise_if_empty=False
    )
    assert set(result) == {'A', 'C'}

def test_get_places_multiple_filters(monkeypatch):
    """get_places handles multiple filter keys and list values correctly."""
    df = pd.DataFrame({
        'dcid': ['c1', 'c2', 'c3', 'c4', 'c5'],
        'name_official': ['A', 'B', 'C', 'D', 'E'],
        'region': ['R1', 'R2', 'R1', 'R2', 'R1'],
        'income_level': ['High', 'High', 'Low', 'Low', 'High']
    })
    monkeypatch.setattr(main._country_resolver, '_concordance_table', df)

    result = main.get_places(
        filters={'region': ['R1', 'R2'], 'income_level': 'High'},
        place_format='name_official',
        raise_if_empty=False
    )
    assert set(result) == {'A', 'B', 'E'}

def test_get_places_empty_warns_and_returns_empty(monkeypatch, caplog):
    """
    When filters are individually valid but yield no rows (R2 & High here),
    get_places logs a warning and returns [].
    """
    df = pd.DataFrame({
        'dcid': ['c1', 'c2', 'c3'],
        'name_official': ['A', 'B', 'C'],
        'region': ['R1', 'R2', 'R1'],
        'income_level': ['High', 'Low', 'Low']
    })
    monkeypatch.setattr(main._country_resolver, '_concordance_table', df)

    caplog.set_level('WARNING', logger='bblocks.places.main')
    result = main.get_places(
        filters={'region': 'R2', 'income_level': 'High'},
        place_format='name_official',
        raise_if_empty=False
    )
    assert result == []
    # Values get coerced to lists in-place
    assert "No places found for filters {'region': ['R2'], 'income_level': ['High']}" in caplog.text

def test_get_places_empty_raises(monkeypatch):
    """
    When filters are individually valid but yield no rows and raise_if_empty=True,
    get_places should raise ValueError.
    """
    df = pd.DataFrame({
        'dcid': ['c1', 'c2', 'c3'],
        'name_official': ['A', 'B', 'C'],
        'region': ['R1', 'R2', 'R1'],
        'income_level': ['High', 'Low', 'Low']
    })
    monkeypatch.setattr(main._country_resolver, '_concordance_table', df)

    with pytest.raises(ValueError) as exc:
        main.get_places(
            filters={'region': 'R2', 'income_level': 'High'},
            place_format='name_official',
            raise_if_empty=True
        )
    assert "No places found for filters {'region': ['R2'], 'income_level': ['High']}" in str(exc.value)

def test_get_places_invalid_place_format():
    """get_places should reject invalid place_format before querying."""
    with pytest.raises(ValueError):
        main.get_places(filters={'region': 'R1'}, place_format='not_a_format')


# --------------------------------------------------
# Tests for resolve_map
# --------------------------------------------------


def test_main_resolve_map_delegates(monkeypatch):
    """main.resolve_map should pass args through to _country_resolver.resolve_map."""
    captured = {}
    def fake_resolve_map(**kwargs):
        captured.update(kwargs)
        return {"X": "x"}
    monkeypatch.setattr(main._country_resolver, "resolve_map", fake_resolve_map)

    places = ["A","B"]
    out = main.resolve_map(
        places,
        to_type="region",
        from_type="name_official",
        not_found="ignore",
        multiple_candidates="first",
        custom_mapping={"A": "override"},
        ignore_nulls=True
    )
    assert out == {"X": "x"}
    assert captured == {
        "places": places,
        "to_type": "region",
        "from_type": "name_official",
        "not_found": "ignore",
        "multiple_candidates": "first",
        "custom_mapping": {"A": "override"},
        "ignore_nulls": True,
    }

def test_main_resolve_map_invalid_from_type():
    """Invalid from_type should error before delegating."""
    with pytest.raises(ValueError):
        main.resolve_map(["A"], from_type="not_a_format")


# --------------------------------------------------
# Tests for filter
# --------------------------------------------------

@pytest.fixture(autouse=True)
def dummy_table(monkeypatch):
    """Provide a dummy concordance table so validation passes."""
    import pandas as pd
    df = pd.DataFrame({
        "dcid": ["c1", "c2"],
        "region": ["R1", "R2"],
        "group": ["G1", "G2"],
    })
    monkeypatch.setattr(main._country_resolver, "_concordance_table", df)
    return df

def test_main_filter_delegates(monkeypatch):
    """main.filter should validate inputs and pass through to _country_resolver.filter."""
    captured = {}
    def fake_filter(**kwargs):
        captured.update(kwargs)
        return ["A", "C"]
    monkeypatch.setattr(main._country_resolver, "filter", fake_filter)

    result = main.filter(
        places=["A", "B", "C"],
        filters={"region": "R1"},
        from_type="name_official",
        not_found="ignore",
        multiple_candidates="last",
        raise_if_empty=True
    )
    assert result == ["A", "C"]
    assert captured == {
        "places": ["A", "B", "C"],
        "filters": {"region": ["R1"]},
        "from_type": "name_official",
        "not_found": "ignore",
        "multiple_candidates": "last",
    }

def test_main_filter_empty_warns_and_returns_empty(monkeypatch, caplog):
    """If resolver.filter returns empty list and raise_if_empty=False, logs a warning."""
    monkeypatch.setattr(main._country_resolver, "filter", lambda **kw: [])
    caplog.set_level(logging.WARNING, logger="bblocks.places.main")

    out = main.filter(
        places=["A", "B"],
        filters={"region": "R1"},
        from_type="name_official",
        raise_if_empty=False
    )
    assert out == []
    assert "No places found for filters {'region': ['R1']}" in caplog.text

def test_main_filter_empty_raises(monkeypatch):
    """If resolver.filter returns empty list and raise_if_empty=True, raises ValueError."""
    monkeypatch.setattr(main._country_resolver, "filter", lambda **kw: [])
    with pytest.raises(ValueError) as exc:
        main.filter(
            places=["A"],
            filters={"region": "R1"},
            from_type="name_official",
            raise_if_empty=True
        )
    assert "No places found for filters {'region': ['R1']}" in str(exc.value)