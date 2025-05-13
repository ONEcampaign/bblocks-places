"""Resolver"""

from os import PathLike
from datacommons_client import DataCommonsClient
from typing import Optional, Literal
import pandas as pd

from bblocks.places.disambiguator import resolve_places_to_dcids
from bblocks.places.concordance import (
    map_candidates,
    map_places,
    validate_concordance_table,
    fetch_properties,
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


CONCORDANCE_DTYPES = {
    "dcid": "string",
    "name_official": "string",
    "name_short": "string",
    "iso2_code": "string",
    "iso3_code": "string",
    "iso_numeric_code": "Int64",  # Nullable integer
    "m49_code": "Int64",
    "region_code": "Int64",
    "region": "string",
    "subregion_code": "Int64",
    "subregion": "string",
    "intermediate_region_code": "Int64",
    "intermediate_region": "string",
    "ldc": "boolean",
    "lldc": "boolean",
    "sids": "boolean",
    "un_member": "boolean",
    "un_observer": "boolean",
    "un_former_member": "boolean",
    "dac_code": "Int64",
    "income_level": "string",
}


class PlaceResolver:
    """A class to resolve places to different formats"""

    # Shared class-level concordance table (loaded once).
    _concordance_table: pd.DataFrame = pd.read_csv(
        Paths.project / "places" / "concordance.csv", dtype=CONCORDANCE_DTYPES
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        dc_instance: Optional[str] = "datacommons.one.org",
        url: Optional[str] = None,
        concordance_table: Optional[
            pd.DataFrame | None | Literal["default"]
        ] = "default",
        *,
        dc_entity_type: Optional[str] = None,
        custom_disambiguation: Optional[dict] = None,
    ):

        self._dc_client = DataCommonsClient(
            api_key=api_key, url=url, dc_instance=dc_instance
        )

        if concordance_table == "default":
            self._concordance_table = self._concordance_table
        else:
            self._concordance_table = concordance_table

        if self._concordance_table is not None:
            validate_concordance_table(
                self._concordance_table
            )  # validate the concordance table

        self._dc_entity_type = dc_entity_type
        self._custom_disambiguation = custom_disambiguation

    def _map_candidates_to_dc_property(self, candidates: dict[str, str | list | None], dc_property: str) -> dict[str, str | list | None]:
        """This runs a concordance operation using the Data Commons Node endpoint.

        It takes a dictionary of candidates where the keys are the original names and the values are the DCIDs.
        It uses the DCIDs to fetch the properties from the Data Commons Node endpoint, then maps the
        property values retrieved to the original names.

        Args:
            candidates: A dictionary of candidates where the keys are the original names and the values are the DCIDs.
            dc_property: The property to fetch from the Data Commons Node endpoint.

        Returns:
            A dictionary of candidates where the keys are the original names and the values are the property values.

        """

        logger.info(f"Mapping to {dc_property} using Data Commons API")

        # get a flattened list of dcids
        dcids = [
            v for val in candidates.values()
            for v in (val if isinstance(val, list) else [val])
        ]
        # fetch the properties from the Data Commons Node endpoint
        dc_props = fetch_properties(self._dc_client, dcids, dc_property)

        # map the property values back to the original names
        for place, val in candidates.items():
            if isinstance(val, str):
                candidates[place] = dc_props.get(val)
            elif isinstance(val, list):
                mapped = [dc_props.get(v) for v in val if dc_props.get(v)]
                candidates[place] = mapped[0] if len(mapped) == 1 else (mapped or None)
            else:
                candidates[place] = None

        return candidates

    def _resolve_with_disambiguation(self, to_type: str, places_to_map: list[str]) -> dict[str, str | list | None]:
        """The mapping pipeline that disambiguates the places and maps them to the desired type.

        This method uses the Data Commons API and/or any custom disambiguation rules
        to disambiguate places, then concords them to the desired type.

        Args:
            to_type: The desired type to map the places to.
            places_to_map: A list of places to map.

        Returns:
            A dictionary of candidates where the keys are the original names and the values are the mapped values.
        """

        # disambiguate the places
        candidates = resolve_places_to_dcids(
            dc_client=self._dc_client,
            entities=places_to_map,
            entity_type=self._dc_entity_type,
            disambiguation_dict=self._custom_disambiguation,
        )

        # if to_type is dcid then there is no need to map the candidates
        if to_type == "dcid":
            return candidates


        # if the to_type is in the concordance table, then map the candidates using the concordance table

        # if the to_type is in the concordance table, then we use the concordance table
        if (
                self._concordance_table is not None
                and to_type in self._concordance_table.columns
        ):
            return map_candidates(
                concordance_table=self._concordance_table,
                candidates=candidates,
                to_type=to_type,
            )

        # else if the to_type is not in the concordance table, then we use Node
        return self._map_candidates_to_dc_property(
                candidates=candidates,
                dc_property=to_type,
            )

    def _resolve_without_disambiguation(self, places_to_map, from_type: str, to_type:str):
        """The mapping pipeline that doesn't require disambiguation.

        This method uses a concordance table or Node to map the places to the desired type, without needing to
        disambiguate them first. If the target type is in the concordance table, it uses that to map the places.
        Otherwise, it uses Node to map the places, by first mapping places to dcid then using the dcid to get the
        desired type.

        Args:
            places_to_map: A list of places to map.
            from_type: The original type of the places.
            to_type: The desired type to map the places to.

        Returns:
            A dictionary of candidates where the keys are the original names and the values are the mapped values.

        """

        # if the from_type is in the concordance table, then use the concordance table to map the places
        if self._concordance_table is not None and to_type in self._concordance_table.columns:
            return map_places(
                concordance_table=self._concordance_table,
                places=places_to_map,
                from_type=from_type,
                to_type=to_type,
            )

        # Otherwise, use Node to map the places

        # Map the places to dcid before using Node
        if from_type != "dcid":
            candidates = map_places(
                concordance_table=self._concordance_table,
                places=places_to_map,
                from_type=from_type,
                to_type="dcid",
            )
        else:
            # if the from_type is already dcid, then no need to map it - create a mapping dict of dcid to dcid
            candidates = {place: place for place in places_to_map}

        # use Node to map the candidates to the desired type
        return self._map_candidates_to_dc_property(candidates, to_type)

    def _resolve(
        self,
        places: list[str],
        from_type: Optional[str] = None,
        to_type: Optional[str] = "dcid",
        not_found: Literal["raise", "ignore"] = "raise",
        multiple_candidates: Literal["raise", "first", "ignore"] = "raise",
        custom_mapping: Optional[dict[str, str]] = None,
    ) -> dict[str, str]:
        """Main helper pipeline to resolve places to a desired type

        This method handles the mapping of places to a desired type, using either
        disambiguation or concordance table. It also handles custom mappings, not found
        places, and multiple candidates. If a target format that is not in the concordance table
        is requested, it uses the Data Commons Node endpoint to resolve to a Data Commons property.

        Args:
            places: A list of places to resolve.
            from_type: The original type of the places. If None, the places will be disambiguated automatically.
            to_type: The desired type to map the places to. Default is "dcid".
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
            A dictionary mapping the places to the desired type.


        """

        # remove any custom mapping from the entities to map
        places_to_map = [p for p in places if not (custom_mapping and p in custom_mapping)]

        if not places_to_map:
            return custom_mapping

        # if from type is not provided, then we need to disambiguate the places
        if not from_type:
            # disambiguate the places
            candidates = self._resolve_with_disambiguation(to_type=to_type, places_to_map=places_to_map)

        # if the from_type is provided but is not in the concordance table, then we need to disambiguate the places
        elif from_type and (self._concordance_table is None or from_type not in self._concordance_table.columns):
            # disambiguate the places
            candidates = self._resolve_with_disambiguation(to_type=to_type, places_to_map=places_to_map)

        # if the from_type is provided and is in the concordance table, then we can use the concordance table to map the places
        else:
           candidates = self._resolve_without_disambiguation(
                places_to_map=places_to_map,
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

    def resolve_map(
        self,
        places: str | list[str] | pd.Series,
        from_type: Optional[str] = None,
        to_type: Optional[str] = "dcid",
        not_found: Literal["raise", "ignore"] = "raise",
        multiple_candidates: Literal["raise", "first", "ignore"] = "raise",
        custom_mapping: Optional[dict[str, str]] = None,
    ) -> dict[str, str | list[str] | None]:
        """Resolve places to a mapping dictionary of {place: resolved}

        This method takes places, it disambiguates them if needed, and maps them to the desired format, then returns
        a dictionary of the original places to the resolved places. It also handles custom mappings, not found
        places, and multiple candidates. The method converts places to the desired format first by checking the
        concordance table, and if the target format is not in the concordance table, it will try to convert to a
        Data Commons property.


        Args:
            places: A place or list of places to resolve.

            from_type: The original format of the places. Default is None.
                If None, the places will be disambiguated automatically using Data Commons

            to_type: The desired format to convert the places to. Default is "dcid".
                If the object contains a concordance table and the to_type is in the concordance table, it will use
                that concordance table to map the places. Otherwise it will use Data Commons to resolve to a
                Data Commons property.

            not_found: How to handle places that could not be resolved. Default is "raise".
                Options are:
                    - "raise": raise an error.
                    - "ignore": keep the value as None.
                    - Any other string to set as the value for not found places.

            multiple_candidates: How to handle cases when a place can be resolved to multiple values.
                Default is "raise". Options are:
                    - "raise": raise an error.
                    - "first": use the first candidate.
                    - "ignore": keep the value as a list.

            custom_mapping: A dictionary of custom mappings to use. If this is provided, it will
                override any other mappings. Disambiguation and concordance will not be run for those places.
                The keys are the original places and the values are the resolved places.

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

        return self._resolve(
            places=places,
            from_type=from_type,
            to_type=to_type,
            not_found=not_found,
            multiple_candidates=multiple_candidates,
            custom_mapping=custom_mapping,
        )

    def resolve(
        self,
        places: str | list[str] | pd.Series,
        from_type: Optional[str] = None,
        to_type: Optional[str] = "dcid",
        not_found: Literal["raise", "ignore"] = "raise",
        multiple_candidates: Literal["raise", "first", "ignore"] = "raise",
        custom_mapping: Optional[dict[str, str]] = None,
    ) -> str | list[str] | pd.Series:
        """Resolve places

        This method takes places, it disambiguates them if needed, and maps them to the desired format.
        It replaces the original places with the resolved places. It handles custom mappings,
        not found places, and multiple candidates. The method converts places to the desired format first by checking the
        concordance table, and if the target format is not in the concordance table, it will try to convert to a
        Data Commons property.

        Args:
            places: A place or list of places to resolve.

            from_type: The original format of the places. Default is None.
                If None, the places will be disambiguated automatically using Data Commons

            to_type: The desired format to convert the places to. Default is "dcid".
                If the object contains a concordance table and the to_type is in the concordance table, it will use
                that concordance table to map the places. Otherwise it will use Data Commons to resolve to a
                Data Commons property.

            not_found: How to handle places that could not be resolved. Default is "raise".
                Options are:
                    - "raise": raise an error.
                    - "ignore": keep the value as None.
                    - Any other string to set as the value for not found places.

            multiple_candidates: How to handle cases when a place can be resolved to multiple values.
                Default is "raise". Options are:
                    - "raise": raise an error.
                    - "first": use the first candidate.
                    - "ignore": keep the value as a list.

            custom_mapping: A dictionary of custom mappings to use. If this is provided, it will
                override any other mappings. Disambiguation and concordance will not be run for those places.
                The keys are the original places and the values are the resolved places.

        Returns:
            Resolved places in the desired format
        """

        # get a mapping dictionary for the places
        mapper = self.resolve_map(
            places=places,
            from_type=from_type,
            to_type=to_type,
            not_found=not_found,
            multiple_candidates=multiple_candidates,
            custom_mapping=custom_mapping,
        )

        # convert back to the original format replacing the original places with the resolved places
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
    # TODO: handle cases when there is no concordance table

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

        mapper = self.resolve_map(
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

    def get_mapping_dict(
        self, from_type: str, to_type: str, include_nulls: bool = False
    ) -> dict[str, str | None]:
        """Get a mapping dictionary for a given from_type and to_type.

        Args:
            from_type: The original format of the places.
            to_type: The desired format to convert the places to.
            include_nulls: Whether to include null values in the mapping. Default is False.

        Returns:
            A dictionary mapping the from_type values to the to_type values.
        """

        if from_type == to_type:
            logger.warning(
                "from_type and to_type are the same. Returning identical mapping."
            )
            d = {v: v for v in self._concordance_table[from_type].dropna().unique()}

        else:
            raw_dict = self._concordance_table.set_index(from_type)[to_type].to_dict()
            d = {k: v for k, v in raw_dict.items()}

        # if include nulls then convert nan to None
        if include_nulls:
            return {k: v if pd.notna(v) else None for k, v in d.items()}

        # remove nan values
        return {k: v for k, v in d.items() if pd.notna(v)}

    # TODO: handle cases when there is no concordance table

    def add_custom_disambiguation(self, custom_disambiguation: dict) -> None:
        """Add custom disambiguation rules to the resolver.

        Args:
            custom_disambiguation: A dictionary of custom disambiguation rules.
                The keys are the place names and the values are the corresponding DCIDs.
        """

        if self._custom_disambiguation is None:
            self._custom_disambiguation = custom_disambiguation
        else:
            self._custom_disambiguation.update(custom_disambiguation)
