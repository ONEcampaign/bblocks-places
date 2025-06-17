"""Tests for the resolver module."""

import pandas as pd
import pytest

from bblocks.places import resolver


# --- handle_not_founds tests ---

@pytest.mark.parametrize(
    "policy,expect_raise,expected",
    [
        ("raise", True, None),
        ("ignore", False, {"A": None}),
        ("missing", False, {"A": "missing"}),
    ],
)
def test_handle_not_founds(policy, expect_raise, expected):
    candidates = {"A": None}
    if expect_raise:
        with pytest.raises(resolver.PlaceNotFoundError):
            resolver.handle_not_founds(candidates, policy)
    else:
        assert resolver.handle_not_founds(candidates, policy) == expected


# --- handle_multiple_candidates tests ---

@pytest.mark.parametrize(
    "policy,expect_raise,expected",
    [
        ("raise", True, None),
        ("first", False, {"A": "x"}),
        ("last", False, {"A": "y"}),
        ("ignore", False, {"A": ["x", "y"]}),
    ],
)
def test_handle_multiple_candidates(policy, expect_raise, expected):
    candidates = {"A": ["x", "y"]}
    if expect_raise:
        with pytest.raises(resolver.MultipleCandidatesError):
            resolver.handle_multiple_candidates(candidates, policy)
    else:
        assert resolver.handle_multiple_candidates(candidates, policy) == expected


def test_handle_multiple_candidates_invalid_option():
    with pytest.raises(ValueError):
        resolver.handle_multiple_candidates({"A": ["x"]}, "bad")


# --- handle_missing_values tests ---

def test_handle_missing_values_returns_same_dict():
    cand = {"A": None, "B": "val"}
    dcid_map = {"A": "id1", "B": "id2"}
    result = resolver.handle_missing_values(cand, dcid_map, "iso3_code")
    assert result == cand


# --- _map_candidates_to_dc_property tests ---

class DummyClient:
    pass


def test_map_candidates_to_dc_property(monkeypatch):
    client = DummyClient()
    candidates = {"A": "id1", "B": ["id2", "id3"], "C": None}

    def fake_fetch_properties(dc_client, dcids, prop):
        assert dc_client is client
        assert prop == "pop"
        return {"id1": "100", "id2": "200", "id3": None}

    monkeypatch.setattr(resolver, "fetch_properties", fake_fetch_properties)

    res = resolver.PlaceResolver.__new__(resolver.PlaceResolver)
    res._dc_client = client

    assert res._map_candidates_to_dc_property(candidates, "pop") == {
        "A": "100",
        "B": "200",
        "C": None,
    }


# --- resolve_map tests ---

class DummyDC:
    pass


def test_resolve_map_with_concordance(monkeypatch):
    monkeypatch.setattr(resolver, "DataCommonsClient", lambda **_: DummyDC())
    df = pd.DataFrame(
        {
            "dcid": ["id1", "id2"],
            "name_official": ["A", "B"],
            "iso3_code": ["AAA", "BBB"],
        }
    )
    r = resolver.PlaceResolver(concordance_table=df)
    result = r.resolve_map(["A", "B"], from_type="name_official", to_type="iso3_code")
    assert result == {"A": "AAA", "B": "BBB"}


def test_resolve_map_with_dc_property(monkeypatch):
    monkeypatch.setattr(resolver, "DataCommonsClient", lambda **_: DummyDC())
    df = pd.DataFrame({"dcid": ["id1", "id2"]})
    r = resolver.PlaceResolver(concordance_table=df)

    def fake_fetch_properties(dc_client, dcids, prop):
        return {"id1": "P1", "id2": None}

    monkeypatch.setattr(resolver, "fetch_properties", fake_fetch_properties)

    result = r.resolve_map(["id1", "id2"], from_type="dcid", to_type="pop")
    assert result == {"id1": "P1", "id2": None}


def test_resolve_map_disambiguation_ignore(monkeypatch):
    monkeypatch.setattr(resolver, "DataCommonsClient", lambda **_: DummyDC())
    df = pd.DataFrame({"dcid": []})
    r = resolver.PlaceResolver(concordance_table=df)

    def fake_resolve(dc_client, entities, entity_type, disambiguation_dict=None):
        return {"X": "idX", "Y": None}

    monkeypatch.setattr(resolver, "resolve_places_to_dcids", fake_resolve)

    result = r.resolve_map(["X", "Y"], to_type="dcid", not_found="ignore")
    assert result == {"X": "idX", "Y": None}
