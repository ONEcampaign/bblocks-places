"""module with functionality to resolve places

Uses the datacommons API to resolve places.

"""

from datacommons_client.client import DataCommonsClient
import datacommons_client.models.resolve
import datacommons_client.models.node
from typing import Optional, Literal

from bblocks_places.config import logger


class PlaceResolver:
    """class that wraps the resolver endpoint to add functionality to convert countries"""


    def __init__(self, dc_instance: str | None = "datacommons.one.org", api_key: str | None = None,  url: str | None = None):
        # instantiate the client specific to the resolve endpoint
        self._client = DataCommonsClient(
            dc_instance=dc_instance,
            api_key=api_key,
            url=url
        )

    def _fetch_candidates(self, places: str | list, place_type: Optional[str] = None) -> dict[str, list[str]]:
        """Get the candidates for places using the resolve endpoint

        Args:
            places: list of places to resolve
            place_type: type of place to resolve

        Returns:
            dictionary with the place as key and the candidates as values in a list
        """

        result = self._client.resolve.fetch_dcids_by_name(places, entity_type=place_type).entities

        return {entity.node: [candidate.dcid for candidate in entity.candidates] for entity in result}



    def _convert_candidates(self, places: dict, to_property: str) -> dict[str, list[str]]:
        """For the returned candidates get the value of a property

        Args:
            places: dictionary with the place as key and the candidates as values in a list
            to_property: property to get the value of

        Returns:
            dictionary with the place as key and converted candidates as values in a list
        """

        # Get all the candidates in a flat list
        candidates = [item for sublist in places.values() for item in sublist]

        # Get the properties for the candidates
        result = self._client.node.fetch_property_values(node_dcids = candidates, properties = to_property)
        mapper = {} # map the candidate to the property value
        for i, j in result.get_properties().items():
            if hasattr(j, "value"):
                mapper.update({i: j.value})
            else:
                mapper.update({i: None})

        return {
            key: [mapper.get(val) for val in vals if mapper.get(val) is not None]
            for key, vals in places.items()
        }

    def _get_conversion_map(self,
                            places_with_candidates: dict[str, list[str]],
                            not_found: Optional[str | Literal["raise"] | None] = "raise",
                            multiple_candidates: Optional[Literal["raise", "first"]] = "raise") -> dict[str, [str | None]]:
        """Get the conversion map for the places with candidates

        This method parses the places and their candidates to create a flat dictionary to map the places to the candidates.
        It handles the following cases:
        - if there is only one candidate, map the place to the candidate
        - if there are no candidates, map the place to the not_found value. By default this is "raise" which raises an error. Other options are None or a string to map the place to.
        - if there are multiple candidates, raise an error or use the first candidate. By default this is "raise" which raises an error. Other options are "first" to use the first candidate.

        Args:
            places_with_candidates: dictionary with the place as key and the candidates as values in a list
            not_found: value to map the place to if there are no candidates. By default this is "raise" which raises an error. Other options are None or a string to map the place to.
            multiple_candidates: value to handle multiple candidates. By default this is "raise" which raises an error. Other options are "first" to use the first candidate.

        Returns:
            dictionary with the place as key and the candidates as values in a list

        Raises:
            ValueError: if there are multiple candidates and multiple_candidates is "raise" TODO: change to custom error
            ValueError: if there are no candidates and not_found is "raise" TODO: change to custom error

        """

        mapper = {} # map the place to the candidate

        for place, candidates in places_with_candidates.items():
            if len(candidates) == 1:
                mapper[place] = candidates[0]

            # when there are no candidates map to the user import or raise error
            if len(candidates) == 0:
                if not_found == "raise":
                    raise ValueError(f"No candidates for {place}") # TODO: change to custom error
                # if not_found is None, map the place to None
                elif not_found is None:
                    logger.warn(f"No candidates for {place}. Mapping to None")
                    mapper[place] = None

                else:
                    logger.warn(f"No candidates for {place}. Mapping to {not_found}")
                    mapper[place] = not_found

            if len(candidates) > 1:
                if multiple_candidates == "raise":
                    raise ValueError(f"Multiple candidates for {place}: {candidates}") # TODO: change to custom error

                # if multiple_candidates is "first", map the place to the first candidate
                if multiple_candidates == "first":
                    logger.warn(f"Multiple candidates for {place}: {candidates}. Using first candidate: {candidates[0]}")
                    mapper[place] = candidates[0]

        return mapper

    def get_candidates(self, places: str | list[str], to: str = "dcid", place_type: str = None) -> dict[str, list[str]]:
        """Get candidates for places

        This method fetches candidates that match the given places in a specific format.

        Args:
            places: The place(s) to resolve
            to: The format to convert the places to. Default is "dcid". Any other Data Commons property can be used. TODO: add a list of custom formats kept locally eg income level
            place_type: The type of place to resolve e.g. Country. Default is None which searches all types of places.

        Returns:
            A dictionary with the place as key and the candidates in a specified format as values in a list.

        """

        # check if the places are a string or a list
        if isinstance(places, str):
            places = [places]

        # remove duplicates
        places_to_convert = list(set(places))

        # fetch the candidates
        result = self._fetch_candidates(places = places_to_convert, place_type = place_type)

        if to == "dcid":
            return result # avoid requesting DCIDs again

        # TODO add functionality for custom formats such as income level

        # convert the candidates to the new format from Data Commons
        return self._convert_candidates(result, to)

    def convert(self, places: str | list[str], to: str = "dcid", place_type: Optional[str]= None,
                not_found: Optional[str | Literal["raise"] | None] = "raise",
                multiple_candidates: Optional[Literal["raise", "first"]] = "raise") -> str | list[str | None]:
        """Convert places to a new format

        This method converts places to a new format using the Data Commons API.

        Args:
            places: The place(s) to convert
            to: The format to convert the places to. Default is "dcid". Any other Data Commons property can be used. TODO: add a list of custom formats kept locally eg income level
            place_type: The type of place to resolve e.g. Country. Default is None which searches all types of places.
            not_found: value to map the place to if there are no candidates. By default this is "raise" which raises an error. Other options are None or a string to map the place to.
            multiple_candidates: value to handle multiple candidates. By default this is "raise" which raises an error. Other options are "first" to use the first candidate.

        Returns:
            A dictionary with the place as key and the converted candidates as values in a list.

        Raises:
            ValueError: if there are multiple candidates and multiple_candidates is "raise" TODO: change to custom error
            ValueError: if there are no candidates and not_found is "raise" TODO: change to custom error
        """

        # Get the candidates for the places
        result = self.get_candidates(places = places, to = to, place_type = place_type)

        # get a mapping of the candidates to the new format
        mapper = self._get_conversion_map(result, not_found = not_found, multiple_candidates = multiple_candidates)

        # convert the places to the new format in their original type e.g. list or str
        if isinstance(places, str):
            return mapper.get(places)
        else:
            return [mapper.get(place) for place in places]
