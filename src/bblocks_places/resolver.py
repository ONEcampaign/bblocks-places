"""Resolver"""

from datacommons_client import DataCommonsClient
from typing import Optional, Literal
import pandas as pd

from bblocks_places.disambiguator import disambiguation_pipeline
from bblocks_places.concordance import map_candidates, map_places
from bblocks_places.config import (
    logger,
    Paths,
    PlaceNotFoundError,
    MultipleCandidatesError,
)


def handle_not_founds(
    candidates: dict[str, str | list | None],
    not_found: Literal["raise", "ignore"] | str,
):
    """Handle not found places"""

    for place, cands in candidates.items():
        # if the candidate is None, then raise an error
        if cands is None:
            if not_found == "raise":
                raise PlaceNotFoundError(f"Place not found: {place}")
            elif not_found == "ignore":
                logger.warn(f"Place not found: {place}")
                continue
            else:
                # set the value of the candidate to the not_found value
                candidates[place] = not_found

    return candidates


def handle_multiple_candidates(
    candidates: dict[str, str | list | None],
    multiple_candidates: Literal["raise", "first", "ignore"],
):
    """Handle multiple candidates for a place"""

    for place, cands in candidates.items():
        # if the candidate is a list, then raise an error
        if isinstance(cands, list):
            if multiple_candidates == "raise":
                raise MultipleCandidatesError(
                    f"Multiple candidates found for {place}: {cands}"
                )
            elif multiple_candidates == "first":
                # set the value of the candidate to the first value in the list
                candidates[place] = cands[0]
                logger.info(
                    f"Multiple candidates found for {place}. Using first candidate: {cands[0]}"
                )
            elif multiple_candidates == "ignore":
                # keep the value of the candidate as a list
                logger.warn(
                    f"Multiple candidates found for {place}. Keeping all candidates: {cands}"
                )

            else:
                raise ValueError(
                    f"Invalid value for multiple_candidates: {multiple_candidates}. Must be one of ['raise', 'first', 'ignore']"
                )

    return candidates


class PlaceResolver:
    """A class to resolve places to different formats"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        dc_instance: Optional[str] = "datacommons.one.org",
        url: Optional[str] = None,
    ):

        self._dc_client = DataCommonsClient(
            api_key=api_key, url=url, dc_instance=dc_instance
        )
        self._concordance_table = pd.read_csv(
            Paths.project / "bblocks_places" / "concordance.csv"
        )

    def _get_mapper(
        self,
        places: list[str],
        source: Optional[str] = None,
        to: Optional[str] = "dcid",
        not_found: Literal["raise", "ignore"] = "raise",
        multiple_candidates: Literal["raise", "first", "ignore"] = "raise",
        custom_mapping: Optional[dict[str, str]] = None,
    ) -> dict[str, str]:
        """Helper function to get the mapper for a list of places"""

        # remove any custom mapping from the entities to map
        if custom_mapping:
            places_to_map = [p for p in places if p not in custom_mapping]
            # if all places are in the custom mapping, then return the custom mapping
            if not places_to_map:
                return custom_mapping

        else:
            places_to_map = places

        # if no source is provided, try to disambiguate the places
        if not source:
            # disambiguate the places
            candidates = disambiguation_pipeline(
                dc_client=self._dc_client, entities=places_to_map, entity_type="Country"
            )

            # map places to desired type
            if to != "dcid":
                candidates = map_candidates(candidates=candidates, target=to)

        # else if the source is provided, then use the concordance table to map
        else:
            candidates = map_places(places=places_to_map, source=source, target=to)

        # handle not found
        candidates = handle_not_founds(candidates=candidates, not_found=not_found)
        # handle multiple candidates
        candidates = handle_multiple_candidates(
            candidates=candidates, multiple_candidates=multiple_candidates
        )

        # if there are any custom mappings, add them to the candidates
        if custom_mapping:
            candidates = candidates | custom_mapping

        return candidates

    def get_mapper(
        self,
        places: str | list[str] | pd.Series,
        from_type: Optional[str] = None,
        to_type: Optional[str] = "dcid",
        not_found: Literal["raise", "ignore"] = "raise",
        multiple_candidates: Literal["raise", "first", "ignore"] = "raise",
        custom_mapping: Optional[dict[str, str]] = None,
    ) -> dict[str, str]:
        """Get a mapper of places to a desired format

        Args:
            places: A place or places to resolve
            from_type: The source of the places. If None, will try to disambiguate the places
            to_type: The desired format to convert the places to. Default is "dcid"
            not_found: What to do if a place is not found. Default is "raise". Options are "raise", "ignore", or a
            string to use as the value for not found places. "ignore" will keep the value as None
            multiple_candidates: What to do if there are multiple candidates for a place. Default is "raise". Options
            are "raise", "first", or "ignore". "first" will use the first candidate, "ignore" will keep the value as a
            list
            custom_mapping: A dictionary of custom mappings to use

        Returns:
            A dictionary mapping the places to the desired format
        """

        # if the places is a list, get a unique list of places
        if isinstance(places, list):
            places = list(set(places))

        # if places is a string, convert it to a list
        if isinstance(places, str):
            places = [places]

        # if places is a pandas series, convert it to a list of unique values
        elif isinstance(places, pd.Series):
            places = list(places.unique())

        else:
            raise ValueError(
                f"Invalid type for places: {type(places)}. Must be one of [str, list[str], pd.Series]"
            )

        return self._get_mapper(
            places=places,
            source=from_type,
            to=to_type,
            not_found=not_found,
            multiple_candidates=multiple_candidates,
            custom_mapping=custom_mapping,
        )

    def convert(
        self,
        places: str | list[str] | pd.Series,
        from_type: Optional[str] = None,
        to_type: Optional[str] = "dcid",
        not_found: Literal["raise", "ignore"] = "raise",
        multiple_candidates: Literal["raise", "first", "ignore"] = "raise",
        custom_mapping: Optional[dict[str, str]] = None,
    ) -> str | list[str] | pd.Series:
        """Convert places to a desired format

        Args:
            places: A place or places to resolve
            from_type: The source of the places. If None, will try to disambiguate the places
            to_type: The desired format to convert the places to. Default is "dcid"
            not_found: What to do if a place is not found. Default is "raise". Options are "raise", "ignore", or a
            string to use as the value for not found places. "ignore" will keep the value as None
            multiple_candidates: What to do if there are multiple candidates for a place. Default is "raise". Options
            are "raise", "first", or "ignore". "first" will use the first candidate, "ignore" will keep the value as a
            list
            custom_mapping: A dictionary of custom mappings to use

        Returns:
            Converted places in the desired format
        """

        mapper = self.get_mapper(
            places=places,
            source=from_type,
            to=to_type,
            not_found=not_found,
            multiple_candidates=multiple_candidates,
            custom_mapping=custom_mapping,
        )

        # convert back to the original format
        if isinstance(places, str):
            return mapper.get(places)

        elif isinstance(places, pd.Series):
            return places.map(mapper)

        else:
            return [mapper.get(p) for p in places]
