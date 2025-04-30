"""Data Commons API wrapper for resolving places to DCIDs and properties."""

from typing import Optional

import pandas as pd
from datacommons_client.client import DataCommonsClient

from bblocks_places.config import (
    NotFoundBehavior,
    MultipleCandidatesBehavior,
)
from bblocks_places.datacommons.process_candidates import (
    map_dcids_to_props,
    parse_ambiguous,
)
from bblocks_places.utils import split_list, clean_string, flatten_dict

_SPECIAL_CASES: dict[str, str] = {
    "france": "country/FRA",
    "caboverde": "country/CPV",
    "antarctica": "antarctica",
    "alandislands": "nuts/FI2",
    "aland": "nuts/FI2",
    "pitcairn": "country/PCN",
    "svalbardandjanmayenislands": "country/SJM",
}


def apply_custom_disambiguation(candidates):
    """Custom logic for edge cases"""

    for place in list(candidates.keys()):
        key = clean_string(place)

        if fix := _SPECIAL_CASES.get(key):
            candidates[place] = fix

    return candidates


class DataCommonsResolver:
    """High-level user-facing interface for place conversion via Data Commons."""

    def __init__(self, client: DataCommonsClient):
        self._client = client

    def get_candidates(
        self,
        places: str | list[str] | pd.Series,
        to: str = "dcid",
        place_type: Optional[str] = None,
    ) -> dict[str, str | list[str] | None]:
        """Get the candidate that match a place or places in a given format

        This method uses the DataCommons API to try to resolve places to a specific
            property value, giving a list of candidates that match each place.

        Args:
            places: The place or places to resolve.
            to: The property to resolve the places to. Default is "dcid".
            place_type: The Data Commons entity type to resolve e.g. Country. Default is None.

        Returns:
            A dictionary mapping each place to its candidates.
        """

        # Get the unique places to resolve
        if isinstance(places, pd.Series):
            unique = places.unique().tolist()
        elif isinstance(places, str):
            unique = [places]
        else:
            unique = list(set(places))

        name_to_dcids = self._client.resolve.fetch_dcids_by_name(
            names=unique, entity_type=place_type
        ).to_flat_dict()

        # If the user wants to resolve to dcid, return the mapping avoiding the next step
        if to == "dcid":
            return flatten_dict(name_to_dcids)

        # If the user wants to resolve to a property, we need to fetch the values for each dcid
        dcids = [dc for vals in name_to_dcids.values() for dc in (vals or [])]
        prop_map = self._client.node.fetch_property_values(
            node_dcids=dcids, properties=to
        )
        name_to_prop = map_dcids_to_props(
            name_to_dcids=name_to_dcids, dcid_to_props=prop_map
        )

        return flatten_dict(name_to_prop)

    def resolve_ambiguous(
        self,
        places: list[str],
        not_found: NotFoundBehavior | str = "raise",
        multiple: MultipleCandidatesBehavior = "raise",
    ) -> dict[str, str | None]:
        """Resolves a list of places to their Data Commons IDs"""

        candidates = {}
        for chunk in split_list(places, 30):
            candidates.update(self.get_candidates(chunk, place_type="Country"))

        candidates = apply_custom_disambiguation(candidates)
        candidates = parse_ambiguous(
            candidates=candidates, to="dcid", not_found=not_found, multiple=multiple
        )

        return candidates

    def convert(
        self,
        places: str | list[str] | pd.Series,
        to: str = "dcid",
        place_type: Optional[str] = None,
        not_found: NotFoundBehavior | str = NotFoundBehavior.RAISE,
        multiple: MultipleCandidatesBehavior = MultipleCandidatesBehavior.RAISE,
    ) -> str | list[str | None] | pd.Series | None:
        """Convert a place or places to a given format

        This method uses the DataCommons API to resolve a place or places to a specific property value.

        Args:
            places: The place or places to resolve.
            to: The property to resolve the places to. Default is "dcid".
            place_type: The Data Commons entity type to resolve e.g. Country. Default is None.
            not_found: Behavior when a place is not found. Default is "raise". Available options are:
              ["raise", "ignore"] or a string to return when not found. "raise" will raise an error, "ignore" will return None.
            multiple: Behavior when multiple candidates are found. Default is "raise". Available options are:
                ["raise", "first", "ignore"]. "raise" will raise an error, "first" will return the first candidate, "ignore" return all candidates.

        Returns:
            The converted places
        """

        flat = self.get_candidates(places, to, place_type)

        parsed = parse_ambiguous(
            candidates=flat.copy(), to=to, not_found=not_found, multiple=multiple
        )

        if isinstance(places, pd.Series):
            return places.map(parsed)
        if isinstance(places, str):
            return parsed.get(places)
        return [parsed.get(p) for p in places]
