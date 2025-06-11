import pytest

from bblocks.places import main as places


def test_get_places_by_empty_warning():
    assert places.get_places_by(by="region", filter_values=[], raise_if_empty=False) == []


def test_get_places_by_empty_raise():
    with pytest.raises(ValueError):
        places.get_places_by(by="region", filter_values=[], raise_if_empty=True)
