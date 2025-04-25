"""Data Commons API wrapper for resolving places to DCIDs and properties."""

from datacommons_client.client import DataCommonsClient
from typing import Optional, Any
import pandas as pd

from bblocks_places.utils import flatten_dict, map_dict
from bblocks_places.config import DataCommonsAPIError, NotFoundBehavior, MultipleCandidatesBehavior


class DataCommonsWrapper:
    """Basic wrapper for Data Commons API calls with custom error handling."""

    def __init__(self,dc_instance: Optional[str] = None,api_key: Optional[str] = None,url: Optional[str] = None):

        self._client = DataCommonsClient(dc_instance=dc_instance,api_key=api_key,url=url)

    def fetch_dcids_by_name(self, names: list[str], entity_type: Optional[str] = None) -> dict[str, list[str]]:
        """Fetch candidate DCIDs for each provided name.

        Args:
            names: List of names to resolve.
            entity_type: Optional entity type of the names such as "Country"

        Returns:
            A dictionary mapping names to lists of DCIDs.

        Raises:
            DataCommonsAPIError: On API call failure.
        """
        try:
            result = self._client.resolve.fetch_dcids_by_name(names=names, entity_type=entity_type ).to_dict()

        except Exception as e:
            raise DataCommonsAPIError(f"Failed to fetch DCIDs for {names}: {e}")

        mapping = {} # Initialize an empty dictionary to store the mapping

        for entity in result.get('entities', []):

            node = entity.get('node')
            cands = entity.get('candidates') or []

            mapping[node] = [c.get('dcid') for c in cands if 'dcid' in c]

        return mapping

    def fetch_property_values(self, dcids: list[str],prop: str) -> dict[str, list[Any]]:
        """Fetch values for a given property across multiple DCIDs.

        Args:
            dcids: List of DCIDs to fetch property values for.
            prop: Property name to fetch values for.

        Returns:
            A dictionary mapping DCIDs to lists of values for the specified property.

        Raises:
            DataCommonsAPIError: On API call failure.
        """
        try:
            result = self._client.node.fetch_property_values(node_dcids=dcids, properties=prop).to_dict()

        except Exception as e:
            raise DataCommonsAPIError(f"Failed to fetch property '{prop}' for {dcids}: {e}")

        mapping = {} # Initialize an empty dictionary to store the mapping
        data = result.get('data', {}) # Extract the data from the result, defaulting to an empty dictionary if not present

        for dcid in dcids:
            entry = data.get(dcid, {})
            if 'arcs' in entry and prop in entry['arcs']:
                nodes = entry['arcs'][prop]['nodes'] or []
                values = [n.get('value', n.get('name')) for n in nodes]
                mapping[dcid] = values
            else:
                mapping[dcid] = []

        # Deduplicate and flatten nested lists
        return flatten_dict(mapping)


class CandidateProcessor:
    """Processes raw DCID and property mappings: flattens, maps, and handles ambiguity."""

    def map_dcids_to_props(self, name_to_dcids: dict[str, list[str]],dcid_to_props: dict[str, Any]) -> dict[str, list[Any]]:
        """Map DCIDs to their properties."""

        return map_dict(name_to_dcids, dcid_to_props)

    def flatten(self, data: dict[str, Any]) -> dict[str, Any]:
        """Flatten a dictionary with lists as values."""

        return flatten_dict(data)

    def parse_ambiguous(
            self,
            candidates: dict[str, Any],
            to: str,
            not_found: NotFoundBehavior | str = NotFoundBehavior.RAISE,
            multiple: MultipleCandidatesBehavior = MultipleCandidatesBehavior.RAISE
    ) -> dict[str, Any]:
        """Parse ambiguous candidates."""

        for name, val in list(candidates.items()):
            if val is None or (isinstance(val, list) and len(val) == 0):
                if not_found == NotFoundBehavior.RAISE:
                    raise ValueError(f"Could not find a '{to}' match for: {name}")
                elif not_found == NotFoundBehavior.IGNORE:
                    candidates[name] = None
                else:
                    candidates[name] = not_found
            elif isinstance(val, list) and len(val) > 1:
                if multiple == MultipleCandidatesBehavior.RAISE:
                    raise ValueError(f"Multiple '{to}' matches for {name}: {val}")
                elif multiple == MultipleCandidatesBehavior.FIRST:
                    candidates[name] = val[0]
        return candidates


class DataCommonsResolver:
    """High-level user-facing interface for place conversion via Data Commons."""

    def __init__( self,dc_instance: Optional[str] = "datacommons.one.org",api_key: Optional[str] = None,url: Optional[str] = None):

        self._resolver = DataCommonsWrapper(dc_instance=dc_instance, api_key=api_key, url=url)
        self._processor = CandidateProcessor()

    def get_candidates(self, places: str | list[str] | pd.Series, to: str = "dcid", place_type: Optional[str] = None) -> dict[str, str | list[str] | None]:
        """Get the candidate that match a place or places in a given format

        This method uses the DataCommons API to try to resolve places to a specific property value, giving a list of candidates that match each place.

        Args:
            places: The place or places to resolve.
            to: The property to resolve the places to. Default is "dcid".
            place_type: The Data Commons entity type to resolve e.g. Country. Default is None.

        Returns:
            A dictionary mapping each place to its candidates.
        """

        # Get the unique places to resolve
        if isinstance(places, pd.Series):
            unique = list(places.unique())
        elif isinstance(places, str):
            unique = [places]
        else:
            unique = places

        name2dcids = self._resolver.fetch_dcids_by_name(
            names=unique,
            entity_type=place_type
        )

        # If the user wants to resolve to dcid, return the mapping avoiding the next step
        if to == "dcid":
            return self._processor.flatten(name2dcids)

        # If the user wants to resolve to a property, we need to fetch the values for each dcid
        dcids = [dc for vals in name2dcids.values() for dc in (vals or [])]
        prop_map = self._resolver.fetch_property_values(dcids, to)
        name2props = self._processor.map_dcids_to_props(name2dcids, prop_map)

        return self._processor.flatten(name2props)

    def convert(
            self,
            places: str | list[str] | pd.Series,
            to: str = "dcid",
            place_type: Optional[str] = None,
            not_found: NotFoundBehavior | str = NotFoundBehavior.RAISE,
            multiple: MultipleCandidatesBehavior = MultipleCandidatesBehavior.RAISE
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
        parsed = self._processor.parse_ambiguous(flat.copy(), to, not_found, multiple)

        if isinstance(places, pd.Series):
            return places.map(parsed)
        if isinstance(places, str):
            return parsed.get(places)
        return [parsed.get(p) for p in places]
