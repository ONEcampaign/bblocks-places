"""Resolver"""

from os import PathLike

from datacommons_client import DataCommonsClient
from typing import Optional, Literal
import pandas as pd

from bblocks.places.disambiguator import disambiguation_pipeline
from bblocks.places.concordance import (
    map_candidates,
    map_places,
    validate_concordance_table,
)
from bblocks.places.config import (
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

    # Shared class-level concordance table (loaded once).
    _concordance_table: pd.DataFrame = pd.read_csv(
        Paths.project / "places" / "concordance.csv"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        dc_instance: Optional[str] = "datacommons.one.org",
        url: Optional[str] = None,
        concordance_table: Optional[pd.DataFrame] = None,
    ):

        self._dc_client = DataCommonsClient(
            api_key=api_key, url=url, dc_instance=dc_instance
        )

        self._concordance_table = (
            concordance_table
            if concordance_table is not None
            else self._concordance_table
        )
        validate_concordance_table(
            self._concordance_table
        )  # validate the concordance table

    def _get_mapper(
        self,
        places: list[str],
        from_type: Optional[str] = None,
        to_type: Optional[str] = "dcid",
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
        if not from_type:
            # disambiguate the places
            candidates = disambiguation_pipeline(
                dc_client=self._dc_client, entities=places_to_map, entity_type="Country"
            )

            # map places to desired type
            if to_type != "dcid":
                candidates = map_candidates(
                    concordance_table=self._concordance_table,
                    candidates=candidates,
                    to_type=to_type,
                )

        # else if the source is provided, then use the concordance table to map
        else:
            candidates = map_places(
                concordance_table=self._concordance_table,
                places=places_to_map,
                from_type=from_type,
                to_type=to_type,
            )

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
        """Get a mapper of places to a desired format.

        Args:
            places: A place or list of places to resolve.

            from_type: The original format of the places. If None, the places will be disambiguated automatically.
                By default, it is None.
                Options are:
                    - "dcid": Data Commons ID.
                    - "name_official": Official name.
                    - "name_short": Short name.
                    - "iso2_code": ISO Alpha 2-letter code.
                    - "iso3_code": ISO Alpha 3-letter code.
                    - "iso_numeric_code": ISO Numeric code.
                    - "dac_code": DAC code.
                    - "m49_code": M49 code.

            to_type: The desired format to convert the places to. Default is "dcid".
                Options are:
                    - Any of the from_type options.
                    - "income_level": Income level.
                    - "region": Region.
                    - "region_code": Region code.
                    - "subregion": Subregion.
                    - "subregion_code": Subregion code.
                    - "intermediate_region": Intermediate region.
                    - "intermediate_region_code": Intermediate region code.

            not_found: What to do if a place is not found. Default is "raise".
                Options are:
                    - "raise": raise an error.
                    - "ignore": keep the value as None.
                    - Any other string to set as the value for not found places.

            multiple_candidates: What to do if there are multiple candidates for a
                place. Default is "raise". Options are:
                    - "raise": raise an error.
                    - "first": use the first candidate.
                    - "ignore": keep the value as a list.

            custom_mapping: A dictionary of custom mappings to use.

        Returns:
            A dictionary mapping the places to the desired format.
        """

        if isinstance(places, str):
            places = [places]

        elif isinstance(places, list):
            places = list(set(places))  # deduplicate

        elif isinstance(places, pd.Series):
            places = list(places.unique())

        else:
            raise ValueError(
                f"Invalid type for places: {type(places)}. Must be one of [str, list[str], pd.Series]"
            )

        return self._get_mapper(
            places=places,
            from_type=from_type,
            to_type=to_type,
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
            places: A place or list of places to resolve.

            from_type: The original format of the places. If None, the places will be disambiguated automatically.
                By default, it is None.
                Options are:
                    - "dcid": Data Commons ID.
                    - "name_official": Official name.
                    - "name_short": Short name.
                    - "iso2_code": ISO Alpha 2-letter code.
                    - "iso3_code": ISO Alpha 3-letter code.
                    - "iso_numeric_code": ISO Numeric code.
                    - "dac_code": DAC code.
                    - "m49_code": M49 code.

            to_type: The desired format to convert the places to. Default is "dcid".
                Options are:
                    - Any of the from_type options.
                    - "income_level": Income level.
                    - "region": Region.
                    - "region_code": Region code.
                    - "subregion": Subregion.
                    - "subregion_code": Subregion code.
                    - "intermediate_region": Intermediate region.
                    - "intermediate_region_code": Intermediate region code.

            not_found: What to do if a place is not found. Default is "raise".
                Options are:
                    - "raise": raise an error.
                    - "ignore": keep the value as None.
                    - Any other string to set as the value for not found places.

            multiple_candidates: What to do if there are multiple candidates for a
                place. Default is "raise". Options are:
                    - "raise": raise an error.
                    - "first": use the first candidate.
                    - "ignore": keep the value as a list.

            custom_mapping: A dictionary of custom mappings to use.

        Returns:
            Converted places in the desired format
        """

        mapper = self.get_mapper(
            places=places,
            from_type=from_type,
            to_type=to_type,
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

    @property
    def concordance_table(self) -> pd.DataFrame:
        """Get the concordance table"""
        return self._concordance_table

    @classmethod
    def from_csv(
        cls,
        csv_path: PathLike,
        api_key: Optional[str] = None,
        dc_instance: Optional[str] = "datacommons.one.org",
        url: Optional[str] = None,
    ) -> "PlaceResolver":
        """Create a PlaceResolver instance using a CSV file for the concordance table.

        Args:
            csv_path: Path to the CSV file containing the concordance table.
            api_key: Optional API key for Data Commons.
            dc_instance: Optional Data Commons instance.
            url: Optional URL for Data Commons.

        Returns:
            PlaceResolver: An instance of PlaceResolver with the specified concordance table.
        """
        concordance_table = pd.read_csv(csv_path)

        return cls(
            api_key=api_key,
            dc_instance=dc_instance,
            url=url,
            concordance_table=concordance_table,
        )

    def filter(
        self,
        places: list[str] | pd.Series,
        filter_type: str,
        filter_values: str | list[str],
        from_type: Optional[str] = None,
        not_found: Literal["raise", "ignore"] = "raise",
        multiple_candidates: Literal["raise", "first", "ignore"] = "raise",
    ):
        """Filters places based on a filter type and filter values.

        Args:
            places: places to filter
            from_type: the original format of the places. If None, the places will be disambiguated automatically.
            filter_type: the place type to filter by. This should be a valid column in the concordance table. e.g. "region"
            filter_values: the values to filter by
            not_found: What to do if a place is not found. Default is "raise".
                Options are:
                    - "raise": raise an error.
                    - "ignore": keep the value as None.
                    - Any other string to set as the value for not found places.
            multiple_candidates: What to do if there are multiple candidates for a
                place. Default is "raise". Options are:
                    - "raise": raise an error.
                    - "first": use the first candidate.
                    - "ignore": keep the value as a list.

        Returns:
            The filtered places
        """

        # ensure filter_type is a valid column in the concordance table
        if filter_type not in self._concordance_table.columns:
            raise ValueError(
                f"Invalid filter type: {filter_type}. Must be a valid field column in the concordance table."
            )

        # ensure filter_values is a list
        if isinstance(filter_values, str):
            filter_values = [filter_values]

        # check that all filter values are in the concordance table column
        if not all(
            val in self._concordance_table[filter_type].unique()
            for val in filter_values
        ):
            raise ValueError(
                f"Invalid filter values: {filter_values}. Must be a valid value in the {filter_type} column of the concordance table."
            )

        # if the places is a list ensure it is unique
        if isinstance(places, list):
            places_to_filter = list(set(places))
        # convert places to a list if it is a pd.Series
        elif isinstance(places, pd.Series):
            places_to_filter = list(places.unique())
        else:
            raise ValueError(
                f"Invalid type for places: {type(places)}. Must be one of [str, list[str], pd.Series]"
            )

        mapper = self.get_mapper(
            places=places_to_filter,
            from_type=from_type,
            to_type=filter_type,
            not_found=not_found,
            multiple_candidates=multiple_candidates,
        )

        # filter the places based on the filter values
        filtered_places = [
            place
            for place, converted_place in mapper.items()
            if converted_place in filter_values
        ]

        # return the filtered in the original format
        if isinstance(places, list):
            return [place for place in places if place in filtered_places]
        return pd.Series(
            [place for place in places if place in filtered_places], index=places.index
        )
