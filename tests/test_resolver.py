import types
import pytest

import bblocks.places.resolver as resolver
from bblocks.places.resolver import PlaceResolver, handle_not_founds, handle_multiple_candidates


def make_resolver(columns=None):
    res = PlaceResolver(concordance_table=None)
    if columns is not None:
        res._concordance_table = types.SimpleNamespace(columns=columns)
    return res


def test_handle_not_founds_raise():
    with pytest.raises(resolver.PlaceNotFoundError):
        handle_not_founds({"A": None}, not_found="raise")


def test_handle_not_founds_ignore():
    result = handle_not_founds({"A": None}, not_found="ignore")
    assert result == {"A": None}


def test_handle_not_founds_custom():
    result = handle_not_founds({"A": None}, not_found="missing")
    assert result == {"A": "missing"}


def test_handle_multiple_candidates_raise():
    with pytest.raises(resolver.MultipleCandidatesError):
        handle_multiple_candidates({"A": [1, 2]}, multiple_candidates="raise")


def test_handle_multiple_candidates_first():
    result = handle_multiple_candidates({"A": ["x", "y"]}, multiple_candidates="first")
    assert result["A"] == "x"


def test_handle_multiple_candidates_ignore():
    result = handle_multiple_candidates({"A": ["x", "y"]}, multiple_candidates="ignore")
    assert result["A"] == ["x", "y"]


def test_map_candidates_to_dc_property():
    res = make_resolver()
    res._dc_client.node.mapping = {"id1": "p1", "id2": "p2", "id3": None}
    candidates = {"A": "id1", "B": ["id2", "id3"], "C": None}
    result = res._map_candidates_to_dc_property(candidates, "prop")
    assert result == {"A": "p1", "B": "p2", "C": None}


def test_resolve_with_disambiguation_paths(monkeypatch):
    res = make_resolver(columns=["iso"])
    monkeypatch.setattr(resolver, "resolve_places_to_dcids", lambda **k: {"A": "id1"})
    monkeypatch.setattr(resolver, "map_candidates", lambda **k: {"A": "mapped"})
    monkeypatch.setattr(resolver.PlaceResolver, "_map_candidates_to_dc_property", lambda self, c, d: {"A": "prop"})

    assert res._resolve_with_disambiguation("dcid", ["A"]) == {"A": "id1"}
    assert res._resolve_with_disambiguation("iso", ["A"]) == {"A": "mapped"}
    res._concordance_table = types.SimpleNamespace(columns=[])
    assert res._resolve_with_disambiguation("prop", ["A"]) == {"A": "prop"}


def test_resolve_without_disambiguation_paths(monkeypatch):
    res = make_resolver(columns=["iso"])
    monkeypatch.setattr(resolver, "map_places", lambda **k: {p: f"{k['to_type']}_{p}" for p in k['places']})
    monkeypatch.setattr(resolver.PlaceResolver, "_map_candidates_to_dc_property", lambda self, c, d: {k: f"prop_{v}" for k, v in c.items()})

    assert res._resolve_without_disambiguation(["A"], "dcid", "iso") == {"A": "iso_A"}
    res._concordance_table = types.SimpleNamespace(columns=[])
    assert res._resolve_without_disambiguation(["A"], "name", "prop") == {"A": "prop_dcid_A"}
    assert res._resolve_without_disambiguation(["A"], "dcid", "prop") == {"A": "prop_A"}
