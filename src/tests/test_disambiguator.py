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


