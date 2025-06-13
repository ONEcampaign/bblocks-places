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
            "B": []            # will normalize [] → None
        }
    }
    client = FakeDCClient(response_map)
    result = disambiguator.fetch_dcids_by_name(client, ["A", "B"], "PlaceType", chunk_size=None)
    assert result == {
        "A": ["dcid/A"],
        "B": None,
    }


def test_fetch_dcids_by_name_chunk_size_zero_behaves_as_no_chunk():
    """
    chunk_size=0 is falsy: should behave like no-chunking.
    """
    response_map = {
        (("X", "Y"), "Type"): {
            "X": ["1"],
            "Y": ["2"]
        }
    }
    client = FakeDCClient(response_map)
    result = disambiguator.fetch_dcids_by_name(client, ["X", "Y"], "Type", chunk_size=0)
    assert result == {"X": ["1"], "Y": ["2"]}


def test_fetch_dcids_by_name_with_chunking_and_normalization():
    """
    With chunk_size > 0, should split into chunks, call API per chunk,
    merge the dicts, and normalize empty lists to None.
    """
    response_map = {
        (("A", "B"), "T"): {
            "A": ["1"],
            "B": []
        },
        (("C",), "T"): {
            "C": ["3"]
        }
    }
    client = FakeDCClient(response_map)
    # chunk_size=2 → splits ["A","B","C"] into ["A","B"] and ["C"]
    result = disambiguator.fetch_dcids_by_name(client, ["A", "B", "C"], "T", chunk_size=2)
    assert result == {
        "A": ["1"],
        "B": None,
        "C": ["3"],
    }