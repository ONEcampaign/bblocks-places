"""Disambiguator tests."""

import pytest

from bblocks.places import disambiguator

# Mocks for DataCommonsClient.resolve.fetch_dcids_by_name in disambiguator tests


class FakeResolveResponse:
    """Simulates the response object with a to_flat_dict() method."""

    def __init__(self, mapping):
        # mapping: dict[str, list[str] or str]
        self._mapping = mapping

    def to_flat_dict(self):
        # Return a copy to avoid mutation in tests
        return dict(self._mapping)


class FakeResolveClient:
    """Simulates the `client.resolve` interface."""

    def __init__(self, response_map):
        """
        response_map: dict[(tuple(entities), entity_type), dict[str, list[str] or str]]
        """
        self._response_map = response_map

    def fetch_dcids_by_name(self, entities, entity_type):
        key = (tuple(entities), entity_type)
        mapping = self._response_map.get(key, {})
        return FakeResolveResponse(mapping)


class FakeDCClient:
    """Simulates the DataCommonsClient for use in disambiguator tests."""

    def __init__(self, response_map):
        # The `.resolve` attribute provides fetch_dcids_by_name(...)
        self.resolve = FakeResolveClient(response_map)


def test_fetch_dcids_by_name_empty_input():
    """
    Empty entities list should return {} without calling the API.
    """
    client = FakeDCClient(response_map={})
    result = disambiguator.fetch_dcids_by_name(client, [], "PlaceType", chunk_size=5)
    assert result == {}


def test_fetch_dcids_by_name_no_chunking_with_none_chunk_size():
    """
    When chunk_size is None, should call API once and return its to_flat_dict(),
    normalizing any empty lists to None.
    """
    response_map = {
        (("A", "B"), "PlaceType"): {
            "A": ["dcid/A"],
            "B": [],  # will normalize [] → None
        }
    }
    client = FakeDCClient(response_map)
    result = disambiguator.fetch_dcids_by_name(
        client, ["A", "B"], "PlaceType", chunk_size=None
    )
    assert result == {
        "A": ["dcid/A"],
        "B": None,
    }


def test_fetch_dcids_by_name_chunk_size_zero_behaves_as_no_chunk():
    """
    chunk_size=0 is falsy: should behave like no-chunking.
    """
    response_map = {(("X", "Y"), "Type"): {"X": ["1"], "Y": ["2"]}}
    client = FakeDCClient(response_map)
    result = disambiguator.fetch_dcids_by_name(client, ["X", "Y"], "Type", chunk_size=0)
    assert result == {"X": ["1"], "Y": ["2"]}


def test_fetch_dcids_by_name_with_chunking_and_normalization():
    """
    With chunk_size > 0, should split into chunks, call API per chunk,
    merge the dicts, and normalize empty lists to None.
    """
    response_map = {
        (("A", "B"), "T"): {"A": ["1"], "B": []},
        (("C",), "T"): {"C": ["3"]},
    }
    client = FakeDCClient(response_map)
    # chunk_size=2 → splits ["A","B","C"] into ["A","B"] and ["C"]
    result = disambiguator.fetch_dcids_by_name(
        client, ["A", "B", "C"], "T", chunk_size=2
    )
    assert result == {
        "A": ["1"],
        "B": None,
        "C": ["3"],
    }


@pytest.mark.parametrize(
    "entity, disamb_dict, expected",
    [
        # Exact match
        ("foo", {"foo": "X"}, "X"),
        # Case-insensitive
        ("FOO", {"foo": "X"}, "X"),
        # ASCII-hyphen punctuation-insensitive
        ("foo bar", {"Foo-Bar": "Y"}, "Y"),
        ("FOO-BAR!", {"Foo-Bar": "Y"}, "Y"),
        # Whitespace trimming
        ("  test  ", {"test": "T"}, "T"),
        # Accent folding
        ("cote", {"Côte": "Z"}, "Z"),
        ("CÔTE", {"Côte": "Z"}, "Z"),
        # Combining-mark normalization
        ("Co\u0302te", {"Côte": "Z"}, "Z"),  # Côte
    ],
)
def test_custom_disambiguation_matches(entity, disamb_dict, expected):
    assert disambiguator.custom_disambiguation(entity, disamb_dict) == expected


def test_custom_disambiguation_missing_returns_none():
    disamb_dict = {"a": "A"}
    assert disambiguator.custom_disambiguation("b", disamb_dict) is None


# --- Tests for resolve_places_to_dcids --- #


def test_resolve_places_empty_list():
    """Empty entities list should give empty result."""
    client = FakeDCClient(response_map={})
    result = disambiguator.resolve_places_to_dcids(client, [], "Type")
    assert result == {}


def test_resolve_places_no_disamb_no_chunk():
    """
    No disambiguation dict and chunk_size=None → single API call,
    raw lists preserved.
    """
    response_map = {(("A", "B"), "T"): {"A": ["1"], "B": ["2"]}}
    client = FakeDCClient(response_map)
    result = disambiguator.resolve_places_to_dcids(
        client, ["A", "B"], "T", disambiguation_dict=None, chunk_size=None
    )
    assert result == {"A": ["1"], "B": ["2"]}


def test_resolve_places_chunking_merges_batches():
    """
    chunk_size>0 splits the list, makes multiple calls, and merges them.
    """
    response_map = {
        (("A", "B"), "T"): {"A": ["1"], "B": ["2"]},
        (("C",), "T"): {"C": ["3"]},
    }
    client = FakeDCClient(response_map)
    # chunk_size=2 → ["A","B"] & ["C"]
    result = disambiguator.resolve_places_to_dcids(
        client, ["A", "B", "C"], "T", disambiguation_dict=None, chunk_size=2
    )
    assert result == {"A": ["1"], "B": ["2"], "C": ["3"]}


def test_resolve_places_with_disambiguation_prefilter():
    """
    Entities in disambiguation_dict are taken first and not sent to API;
    the rest are fetched.
    """
    response_map = {(("Y",), "T"): {"Y": ["yid"]}}
    client = FakeDCClient(response_map)
    disamb = {"X": "xid"}
    result = disambiguator.resolve_places_to_dcids(
        client, ["X", "Y"], "T", disambiguation_dict=disamb, chunk_size=None
    )
    assert result == {"X": "xid", "Y": ["yid"]}


def test_resolve_places_not_found_becomes_none():
    """
    If the API returns no entries for the requested entities,
    resolve_places_to_dcids should return an empty dict (no keys).
    """
    response_map = {(("Z",), "T"): {}}  # server returns no mapping for "Z"
    client = FakeDCClient(response_map)
    result = disambiguator.resolve_places_to_dcids(
        client, ["Z"], "T", disambiguation_dict=None, chunk_size=None
    )
    assert result == {}


def test_fetch_dcids_handles_dcstatuserror_and_sets_none(monkeypatch):
    """When bulk call raises DCStatusError, unresolved entities map to None."""

    def raise_for_bulk(entities, entity_type):
        if isinstance(entities, (list, tuple)) and len(entities) > 1:
            raise disambiguator.DCStatusError("boom")
        if entities == "A":
            return FakeResolveResponse({"A": ["dcid/A"]})
        raise Exception("not resolvable")

    client = FakeDCClient(response_map={})
    monkeypatch.setattr(client.resolve, "fetch_dcids_by_name", raise_for_bulk)

    result = disambiguator.fetch_dcids_by_name(client, ["A", "B"], "T", chunk_size=None)

    assert result["B"] is None


def test_fetch_dcids_handles_dcstatuserror_with_chunking(monkeypatch):
    """Chunked call raising DCStatusError resolves items individually."""

    def raise_for_chunk(entities, entity_type):
        if isinstance(entities, (list, tuple)) and len(entities) > 1:
            raise disambiguator.DCStatusError("boom")
        if entities == "A":
            return FakeResolveResponse({"A": ["dcid/A"]})
        raise Exception("not resolvable")

    client = FakeDCClient(response_map={})
    monkeypatch.setattr(client.resolve, "fetch_dcids_by_name", raise_for_chunk)

    result = disambiguator.fetch_dcids_by_name(client, ["A", "B"], "T", chunk_size=2)

    assert result == {"A": ["dcid/A"], "B": None}
