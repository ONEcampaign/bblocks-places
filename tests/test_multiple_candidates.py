import pytest
import types
import sys

sys.modules.setdefault(
    "datacommons_client",
    types.SimpleNamespace(DataCommonsClient=lambda **kwargs: None),
)

from bblocks.places import resolver


def test_handle_multiple_candidates_last():
    candidates = {"place": ["a", "b", "c"]}
    result = resolver.handle_multiple_candidates(candidates, "last")
    assert result["place"] == "c"
