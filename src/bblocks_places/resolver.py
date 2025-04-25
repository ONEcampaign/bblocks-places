"""Module to resolve places to their Data Commons IDs and other properties."""

from datacommons_client.client import DataCommonsClient
from typing import Optional, Literal
import pandas as pd

from bblocks_places.config import logger


def _remove_duplicates_in_place(lst: list[str | list | None]) -> None:
    """Remove duplicate values from a list in-place, preserving order.
    Works with unhashable and nested items (e.g. lists, dicts).

    Args:
        lst: The list to remove duplicates from.

    Returns:
        None: The list is modified in-place.
    """
    seen = []
    for item in lst:
        if item not in seen:
            seen.append(item)
    lst[:] = seen


def flatten_dict(d: dict[str: list[str, None]]) -> dict[str, str | None | list[str]]:
    """Take a dictionary with values as a list and flatten it.

    - If the list is empty, set the value to None
    - If there are null values in the list, remove them
    """

    # if the dictionary is empty, return an empty dictionary
    if not d:
        return {}

    # loop through the dictionary
    for k, v in d.items():

        # remove any duplicates from the list
        _remove_duplicates_in_place(v)

        # check if there are any Nones in the list and remove them
        for i in v:
            if i is None:
                v.remove(i)

        # check if the list is empty
        if not v:
            d[k] = None

        # if there is only 1 value, return it as a string
        elif len(v) == 1:
            d[k] = v[0]

        # if there are multiple values, return it as a list
        elif len(v) > 1:
            d[k] = v

    return d


#function to map values in dict 2 to the values in dict 1
def map_dict(dict1: dict, dict2: dict) -> dict[str, list[str]]:
    """Map the values in s second dictionary to the values in the first dictionary where the
    values in the first dictionary are the keys in the second dictionary.

    e.g.
    dict1 ={
        'a': ['b', 'c'],
        'b': ['d', 'e']
    }

    dict2 = {
        'b': 'x',
        'c': 'y',
        'd': 'z'
    }

    map_dict(dict1, dict2) = {
        'a': ['x', 'y'],
        'b': ['z']
    }
    """

    return {
        k: [dict2[id_] for id_ in v if id_ in dict2]
        for k, v in dict1.items()
    }


class PlaceResolver:
    """A class to resolve places to their Data Commons IDs and other properties."""

    def __init__(self,
                 dc_instance: str | None = "datacommons.one.org",
                 api_key: str | None = None,
                 url: str | None = None):

        self._client = DataCommonsClient(dc_instance=dc_instance, api_key=api_key, url=url)

    def _fetch_dcid_candidates(self, places, place_type = None) -> dict[str, list[str]]:
        """Return a dictionary mapping places to dcid candidates

        Args:
            places: The place or list of places to convert
            place_type: The type of place to convert to. This must be a Data Commons entity type for example Country

        Returns:
            A dictionary mapping the places to the dcid candidates
        """

        result = self._client.resolve.fetch_dcids_by_name(names=places, entity_type=place_type).to_dict()
        return {i['node']: [j['dcid'] if len(j)>0 else None
                    for j in i['candidates']]
                for i in result['entities']
                }

    def _fetch_property_map(self, dcids: list[str], dc_property: str) -> dict[str, list[str]]:
        """Fetch the property map for a list of dcids and a property

        Args:
            dcids: The list of dcids to fetch the property map for
            dc_property: The property to fetch the map for

        Returns:
            A dictionary mapping the dcids to the property values
        """

        result = self._client.node.fetch_property_values(node_dcids=dcids, properties=dc_property).to_dict()

        # Get the properties for the dcids
        d = {}
        for dcid, value in result['data'].items():
            if "arcs" in value:
                d[dcid] = [node['value'] if "value" in node else node['name'] for node in value['arcs'][dc_property]['nodes']]
            else:
                logger.debug(f"Property {dc_property} not found for {dcid}. Resolving to None")

        return flatten_dict(d)


    def get_candidates(self,
                       places: str | list[str] | pd.Series,
                       to: Optional[str] = "dcid",
                       place_type: Optional[str] = None
                       ) -> dict[str, str | None | list[str]]:
        """Get the candidates a place or places in a specified format

        Args:
            places: The place or list of places to convert
            to: The format to convert to. Defaults to "dcid" which is the DataCommons ID.
            place_type: The type of place to convert to. This must be a Data Commons entity type for example Country

        Returns:
            A dictionary mapping the places to the candidates in the specified format
        """

        if isinstance(places, pd.Series):
            places = list(places.unique())

        # fetch the dcid candidates for the places
        places_dcids_dict = self._fetch_dcid_candidates(places, place_type)

        if to == "dcid":
            return flatten_dict(places_dcids_dict)

        # get a list of all the dcids
        dcids_list = [item for v in places_dcids_dict.values() if v for item in v]

        # get the properties for the dcids
        dcids_dict = self._fetch_property_map(dcids_list, to)

        # map the values in the dcids_dict to the values in the places_dcids_dict
        mapped_dict = map_dict(places_dcids_dict, dcids_dict)

        # flatten the dictionary
        mapped_dict = flatten_dict(mapped_dict)

        return mapped_dict

    @staticmethod
    def _parse_ambiguous_candidates(candidates: dict,
                                    to:str,
                                    not_found: Optional[Literal["raise", "ignore"] | str] = "raise",
                                    multiple_candidates: Optional[Literal["raise", "first", "ignore"]] = "raise",) -> dict:
        """Parse the candidates to check if there are any ambiguous candidates or not found candidates and handle them how the user wants

        Args:
            candidates: The candidates to parse
            to: The format the candidates are converted to
            not_found: How to handle not found candidates. Can be "raise", "ignore" or a string to set the value to.
            multiple_candidates: How to handle multiple candidates. Can be "raise", "first" or "ignore".

        Returns:
            The parsed candidates
        """

        for k,v in candidates.items():

            # if the candidate is not found
            if v is None:
                if not_found == "raise":
                    raise ValueError(f'Could not find a "{to}" match for: {k} ')
                elif not_found == "ignore":
                    logger.warn(f'Could not find a "{to}" match for: {k}. Ignoring. The value will be set to None')
                else:
                    logger.warn(f'Could not find a "{to}" match for: {k}. The value will be set to {not_found}')
                    candidates[k] = not_found

            # if there are multiple candidates
            elif isinstance(v, list):
                if multiple_candidates == "raise":
                    raise ValueError(f'Found multiple "{to}" matches for: {k}. Found: {v}')
                elif multiple_candidates == "first":
                    logger.warn(f'Found multiple matches for "{to}" for: {k}. Using the first match: {v[0]}')
                    candidates[k] = v[0]
                elif multiple_candidates == "ignore":
                    logger.warn(f'Found multiple "{to}" matches for: {k}. All candidates will be used: {v}')

        return candidates

    def split_custom_mapping(self, places: list | str, custom_mapping: dict):
        """Removes places that are listed in the custom mapping from the list of places to convert"""

        if isinstance(places,str):
            places = [places]

        places_to_convert = [place for place in places if place not in custom_mapping.keys()]
        return places_to_convert

    def convert(self,
                places: str | list[str] | pd.Series,
                to: str = "dcid",
                place_type: Optional[str] = None,
                not_found: Optional[Literal["raise", "ignore"] | str] = "raise",
                multiple_candidates: Optional[Literal["raise", "first", "ignore"]] = "raise",
                custom_mapping: Optional[dict] = None
                ) -> str | list[str] | None | pd.Series:
        """Convert a place or list of places to a specified format

        Args:
            places: The place or list of places to convert
            to: The format to convert to. Can be a string or a list of strings. Defaults to "dcid" which is the DataCommons ID.
            place_type: The type of place to convert to. This must be a Data Commons entity type for example Country
            not_found: How to handle not found candidates. Can be "raise", "ignore" or a string to set the value to. Defaults to "raise". "Raise" will raise an error if a place is not found, "ignore" will ignore the place and set the value to None, and a string will set the value to that string.

        """

        # check the type passed for places
        if not isinstance(places, (str, list, pd.Series)):
            raise TypeError(f"places must be a string, list or pandas series. Type passed: {type(places)}")


        # make a copy of the places to convert
        places_to_convert = places

        # if the places are a pandas series, convert them to a list of unique values
        if isinstance(places_to_convert, pd.Series):
            places_to_convert = list(places_to_convert.unique())


        # if there are any custom mappings remove them from the places that need to be converted
        if custom_mapping:

            # when the places are a string
            if isinstance(places, str) and places in custom_mapping:
                return custom_mapping[places]
                # otherwise change the string to a list
            places_to_convert = self.split_custom_mapping(places, custom_mapping)


        # get the candidates for the places
        candidates = self.get_candidates(places=places_to_convert, to=to, place_type=place_type)

        # check if the candidates are ambiguous or not found
        candidates = self._parse_ambiguous_candidates(candidates=candidates, to=to, not_found=not_found, multiple_candidates=multiple_candidates)

        # if there are any custom mappings, add them to the candidates
        if custom_mapping:
            candidates = candidates | custom_mapping


        if isinstance(places, list):
            return [candidates.get(p, p) for p in places]

        if isinstance(places, str):
            return candidates.get(places, places)

        if isinstance(places, pd.Series):
            # map the candidates to the series
            return places.map(candidates)

