from bblocks.places.disambiguator import (
    custom_disambiguation,
    fetch_dcids_by_name,
    resolve_places_to_dcids,
)
from bblocks.places.resolver import PlaceResolver
from datacommons_client import DataCommonsClient


def test_custom_disambiguation():
    mapping = {"Congo": "country/COG"}
    assert custom_disambiguation("Congo", mapping) == "country/COG"
    assert custom_disambiguation("congo", mapping) == "country/COG"
    assert custom_disambiguation("Unknown", mapping) is None


def test_fetch_dcids_by_name_chunked():
    client = DataCommonsClient()
    client.resolve.mapping = {"Zimbabwe": "country/ZWE", "Italy": "country/ITA"}
    result = fetch_dcids_by_name(client, ["Zimbabwe", "Italy"], "Country", chunk_size=1)
    assert result == {"Zimbabwe": "country/ZWE", "Italy": "country/ITA"}


def test_resolve_places_to_dcids(monkeypatch):
    client = DataCommonsClient()
    client.resolve.mapping = {"Italy": "country/ITA", "Kenya": None}
    disamb = {"Congo": "country/COG"}
    result = resolve_places_to_dcids(
        client, ["Italy", "Congo", "Kenya"], "Country", disambiguation_dict=disamb
    )
    assert result == {
        "Italy": "country/ITA",
        "Congo": "country/COG",
        "Kenya": None,
    }
