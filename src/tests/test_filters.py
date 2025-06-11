import pytest

from bblocks.places.main import filter_places_multiple


def test_filter_places_multiple():
    countries = [
        "Zimbabwe",
        "Italy",
        "Botswana",
        "United States",
        "Seychelles",
    ]

    filtered = filter_places_multiple(
        countries,
        filters={"region": "Africa", "income_level": "High income"},
    )

    assert filtered == ["Seychelles"]


def test_filter_places_multiple_preserves_duplicates():
    countries = ["Seychelles", "Zimbabwe", "Seychelles"]

    filtered = filter_places_multiple(
        countries,
        filters={"region": "Africa", "income_level": "High income"},
    )

    assert filtered == ["Seychelles", "Seychelles"]
