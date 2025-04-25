""" """

from datacommons_client.client import DataCommonsClient
from typing import Optional, Literal, Any, Dict, List, Union

import pandas as pd
from bblocks_places.utils import flatten_dict, map_dict


class DataCommonsResolver:
    """Basic wrapper for Data Commons API calls without retry logic."""

    def __init__(
            self,
            dc_instance: Optional[str] = "datacommons.one.org",
            api_key: Optional[str] = None,
            url: Optional[str] = None
    ):
        self._client = DataCommonsClient(
            dc_instance=dc_instance,
            api_key=api_key,
            url=url
        )

    def fetch_dcids_by_name(self, names: List[str], entity_type: Optional[str] = None) -> Dict[str, List[str]]:
        """Fetch candidate DCIDs for each provided name.

        Args:
            names: List of place names to resolve.
            entity_type: Optional Data Commons entity type filter (e.g., 'Country').

        Returns:
            Mapping of each name to a list of DCID candidates (empty if none found).
        """

        # if not isinstance(names, list):
        #     raise ValueError(f"names must be a list of strings, got {type(names)}")

        result = self._client.resolve.fetch_dcids_by_name(
            names=names,
            entity_type=entity_type
        ).to_dict()

        mapping: Dict[str, List[str]] = {}
        for entity in result.get('entities', []):
            node = entity.get('node')
            cands = entity.get('candidates') or []
            dcids = [c.get('dcid') for c in cands if 'dcid' in c]
            mapping[node] = dcids
        return mapping

    def fetch_property_values( self, dcids: List[str], prop: str) -> Dict[str, List[Any]]:
        """
        Fetch values for a given property across multiple DCIDs.

        Args:
            dcids: List of Data Commons IDs.
            prop: Property to retrieve (e.g. 'name', 'isoCode').

        Returns:
            Mapping of each DCID to a list of property values (empty if not available).
        """
        # if not isinstance(dcids, list) or not all(isinstance(d, str) for d in dcids):
        #     raise ValueError(f"dcids must be a list of strings, got {dcids}")

        result = self._client.node.fetch_property_values(
            node_dcids=dcids,
            properties=prop
        ).to_dict()

        mapping: Dict[str, List[Any]] = {}
        data = result.get('data', {})
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
    """Processes resolve responses: flattens, maps, and handles ambiguity."""

    def map_dcids_to_props(self,name_to_dcids: Dict[str, List[str]],dcid_to_props: Dict[str, Any]) -> Dict[str, List[Any]]:
        """Map each input name to its property values via intermediate DCIDs."""

        return map_dict(name_to_dcids, dcid_to_props)

    def flatten(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure that lists are deduplicated and singletons are unwrapped."""

        return flatten_dict(data)

    def parse_ambiguous(self,candidates: Dict[str, Any],to: str,
                        not_found: Optional[Literal['raise', 'ignore'] | str] = 'raise',
                        multiple: Optional[Literal['raise', 'first', 'ignore']] = 'raise') -> Dict[str, Any]:
        """Handle missing or multiple matches according to user preference."""

        for name, val in list(candidates.items()):
            # Handle missing
            if val is None or (isinstance(val, list) and len(val) == 0):
                if not_found == 'raise':
                    raise ValueError(f"Could not find a '{to}' match for: {name}")
                elif not_found == 'ignore':
                    candidates[name] = None
                else:
                    candidates[name] = not_found
            # Handle multiple
            elif isinstance(val, list) and len(val) > 1:
                if multiple == 'raise':
                    raise ValueError(f"Multiple '{to}' matches for {name}: {val}")
                elif multiple == 'first':
                    candidates[name] = val[0]
                # 'ignore' keeps full list
        return candidates


class DataCommonsService:
    """High-level user-facing interface for place conversion via Data Commons."""

    def __init__(
            self,
            dc_instance: Optional[str] = "datacommons.one.org",
            api_key: Optional[str] = None,
            url: Optional[str] = None
    ):
        # Initialize internal resolver and processor
        self._resolver = DataCommonsResolver(
            dc_instance=dc_instance,
            api_key=api_key,
            url=url
        )
        self._processor = CandidateProcessor()

    def get_candidates(
            self,
            places: Union[str, List[str], pd.Series],
            to: str = "dcid",
            place_type: Optional[str] = None
    ) -> Dict[str, Union[str, List[str], None]]:
        """Retrieve raw candidate mappings for places."""
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

        if to == "dcid":
            return self._processor.flatten(name2dcids)

        dcids = [dc for vals in name2dcids.values() for dc in (vals or [])]
        prop_map = self._resolver.fetch_property_values(dcids, to)
        name2props = self._processor.map_dcids_to_props(name2dcids, prop_map)
        return self._processor.flatten(name2props)

    def convert(
            self,
            places: Union[str, List[str], pd.Series],
            to: str = "dcid",
            place_type: Optional[str] = None,
            not_found: Optional[Literal["raise", "ignore"] | str] = "raise",
            multiple: Optional[Literal["raise", "first", "ignore"]] = "raise"
    ) -> Union[str, List[Union[str, None]], pd.Series, None]:
        """Convert places to the target format, handling missing or multiple candidates."""
        flat = self.get_candidates(places, to, place_type)
        parsed = self._processor.parse_ambiguous(flat.copy(), to, not_found, multiple)

        if isinstance(places, pd.Series):
            return places.map(parsed)
        if isinstance(places, str):
            return parsed.get(places)
        return [parsed.get(p) for p in places]
