"""Provides the core functionality to resolve places to standard formats
This module contains the PlaceResolver class which is used to resolve places to standard formats
using Data Commons and/or a custom concordance table
"""

from os import PathLike
from datacommons_client import DataCommonsClient
from typing import Optional, Literal
import pandas as pd

from importlib import resources

from bblocks.places.disambiguator import resolve_places_to_dcids
from bblocks.places.concordance import (
    map_candidates,
    map_places,
    validate_concordance_table,
    fetch_properties,
)
from bblocks.places.config import (
    logger,
    PlaceNotFoundError,
    MultipleCandidatesError,
)

# Default concordance table dtypes
DEFAULT_CONCORDANCE_DTYPES: dict = {
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
    "m49_member": "boolean",
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


def handle_not_founds(
    candidates: dict[str, str | list | None],
    not_found: Literal["raise", "ignore"] | str,
) -> dict[str, str | list | None]:
    """Handle places that could not be resolved

    Args:
        candidates: A dict of candidates.
        not_found: How to handle not founds.
            Options are:
            - `raise`: raise an error.
            - `ignore`: keep the value as None.
            - Any other string to set as the value for not found places.

    Returns:
        The candidates with not found places handled

    Raises:
        PlaceNotFoundError if the function is set to raise an error when places cannot be resolved

    """

    for place, cands in candidates.items():
        # if the candidate is None, then raise an error
        if cands is None:
            if not_found == "raise":
                raise PlaceNotFoundError(f"Place not found: {place}")
            elif not_found == "ignore":
                logger.warning(f"Place not found: {place}. Resolving to None")
                continue
            else:
                # set the value of the candidate to the not_found value
                candidates[place] = not_found
                logger.warning(f"Place not found: {place}. Resolving to: {not_found}")

    return candidates


def handle_multiple_candidates(
    candidates: dict[str, str | list | None],
    multiple_candidates: Literal["raise", "first", "last", "ignore"],
) -> dict[str, str | list | None]:
    """Handle cases when a place can be resolved to more than one value

    Args:
        candidates: A dict of candidates.
        multiple_candidates: How to handle multiple candidates.
            Options are:
                - "raise": raise an error.
                - "first": use the first candidate.
                - "last": use the last candidate.
                - "ignore": keep the value as a list.

    Returns:
        The candidates with multiple candidate values handled

    Raises:
        MultipleCandidatesError if the function is set to raise an error when multiple candidates exist

    """

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
            elif multiple_candidates == "last":
                # set the value of the candidate to the last value in the list
                candidates[place] = cands[-1]
                logger.info(
                    f"Multiple candidates found for {place}. Using last candidate: {cands[-1]}"
                )
            elif multiple_candidates == "ignore":
                # keep the value of the candidate as a list
                logger.warning(
                    f"Multiple candidates found for {place}. Keeping all candidates: {cands}"
                )

            else:
                raise ValueError(
                    f"Invalid value for multiple_candidates: {multiple_candidates}. Must be one of ['raise', 'first', 'last', 'ignore']"
                )

    return candidates


def read_default_concordance_table() -> pd.DataFrame:
    """Read the default concordance table"""

    path = resources.files("bblocks.places").joinpath("concordance.csv")
    return pd.read_csv(path, dtype=DEFAULT_CONCORDANCE_DTYPES)


class PlaceResolver:
    """A class to resolve places

    This object contains functionality to resolve places to standard formats like DCIDs, ISO3 codes, names, etc. It
    uses Data Commons and/or a custom concordance table to resolve places.
    A concordance table can be specified which contains custom mappings of DCIDS to other place formats, for any
    number of places. A default concordance table is provided which contains standard formats used by the ONE
    Campaign. This default concordance table can be used by instantiating the class with the concordance_table
    parameter set to "default". The concordance table can also be set to None, in which case the class will
    be instantiated without a concordance table and will rely entirely on Data Commons to resolve places. Otherwise,
    a custom concordance table can be provided as a pandas DataFrame. If places need to be resolved to formats not
    contained by the concordance table, the format will attempt to be resolved using Data Commons. The object
    also contains disambiguation logic. Disambiguation is handled using Data Commons, but custom
    disambiguation rules can be provided. Default custom disambiguation rules are provided for edge cases that are
    specific to working with countries based on the M49 list of countries and the current functionality of the
    Data Commons API. If any custom disambiguation rules are provided, they will take precedence over the default
    disambiguation logic that uses Data Commons. To set the custom disambiguation rules, instantiate the class with
    the custom_disambiguation parameter set to a dictionary of custom disambiguation rules (a dictionary
    of place names and their corresponding DCIDs). Optionally, you can use the default disambiguation rules by
    setting the custom_disambiguation parameter to "default". Once instantiated, additional custom disambiguation rules
    can be added to the object calling the add_custom_disambiguation method.

    Parameters:
        concordance_table: A pandas DataFrame containing the concordance table. Default is None.
            If "default", the default concordance table will be used. If None, no concordance table will be used.
        custom_disambiguation: A dictionary of custom disambiguation rules. Default is None.
            If "default", the default disambiguation rules will be used. If None, no custom disambiguation rules
            will be used.
        dc_entity_type: The Data Commons entity type to resolve for, for example "Country".
            Default is None. If None, the entity type will be automatically determined.
        dc_api_settings: A dictionary of settings to pass to the Data Commons client. Default is None. If None, the
            ONE Campaign Data Commons instance will be used. Available settings are:
                api_key – The API key for authentication
                dc_instance – The Data Commons instance to use. Defaults to "datacommons.one.org" if not set
                url – A custom, fully resolved URL for the Data Commons API. Defaults to None if not set

    Usage:

    Instantiate an object

    >>> resolver = PlaceResolver()
    This will instantiate a class without a concordance table or custom disambiguation rules. It will also connect to
    the ONE Campaign data commons instance to resolve places.

    >>> resolver = PlaceResolver(concordance_table="default", custom_disambiguation="default", dc_entity_type="Country")
    This will instantiate a class with the default concordance table and default disambiguation rules. It will also
    connect to the ONE Campaign data commons instance to resolve places and will resolve places to
    the "Country" entity type.

    Resolving places:

    The `resolve_map` method will return a dictionary of the original places to the resolved places. For example:

    >>> resolver.map_places(["Zimbabwe", "Italy"], to_type="countryAlpha3Code")
    >>> # returns {"Zimbabwe": "ZWE", "Italy": "ITA"}

    If you know the original format of the places, and they are specified in the concordance table, you can
    specify the from_type parameter. For example,
    >>> resolver.map_places(["Zimbabwe", "Italy"], from_type="name_official", to_type="countryAlpha3Code")

    If there is no concordance table or if the `to_type` is not in the concordance table, the method will
    attempt to resolve the places using Data Commons. As in above, "countryAlpha3Code" is not in the concordance table,
    so the method will attempt to resolve the places using Data Commons. If the `from_type` is not in the concordance
    the method will again try to disambiguate the places using Data Commons.

    There may be cases when a place cannot be resolved to a value. By default the method will raise an error. But you
    can choose how to handle these cases. Options include "ignore" which sets the value to None, or any other string
    which will set the value to that string. For example, if you want to ignore not found places, you can do:
    >>> resolver.map_places(["Zimbabwe", "some invalid place"], to_type="countryAlpha3Code", not_found="ignore")
    >>> # returns {"Zimbabwe": "ZWE", "some invalid place": None}

    Or if you want to set the value to "not found", you can do:
    >>> resolver.map_places(["Zimbabwe", "some invalid place"], to_type="countryAlpha3Code", not_found="not found")
    >>> # returns {"Zimbabwe": "ZWE", "some invalid place": "not found"}

    There may be cases when a place can be resolved to more than one value. By default the method will raise an error.
    But you can choose how to handle these cases. Options include "ignore" which keeps the value as a list containing
    all the candidates, or "first" which will use the first candidate. For example, if you want to ignore multiple
    candidates, you can do:
    >>> resolver.map_places(["Zimbabwe", "Place multiple"], to_type="countryAlpha3Code", multiple_candidates="ignore")
    >>> # returns {"Zimbabwe": "ZWE", "Place multiple": ["candidate1", "candidate2"]}

    Or if you want to use the first candidate, you can do:
    >>> resolver.map_places(["Zimbabwe", "Place multiple"], to_type="countryAlpha3Code", multiple_candidates="first")
    >>> # returns {"Zimbabwe": "ZWE", "Place multiple": "candidate1"}

    Additionally any custom mappings can be provided. For example, if you want to map "Zimbabwe" to "ZIM", you can do:
    >>> resolver.map_places(["Zimbabwe", "Italy"], to_type="countryAlpha3Code", custom_mapping={"Zimbabwe": "ZIM"})
    >>> # returns {"Zimbabwe": "ZIM", "Italy": "ITA"}

    The custom mapping will override any other mappings. Disambiguation and concordance will not be run for
    those places.

    The `resolve` functions the same way but will override original places with the resolved places in their original
    format. For example:
    >>> resolver.resolve_places(["Zimbabwe", "Italy"], to_type="countryAlpha3Code")
    >>> # returns ["ZWE", "ITA"]

    A single string can also be passed to the `resolve` method. For example:
    >>> resolver.resolve_places("Zimbabwe", to_type="countryAlpha3Code")
    >>> # returns "ZWE"

    Or a pandas Series:
    >>> resolver.resolve_places(pd.Series(["Zimbabwe", "Italy"]), to_type="countryAlpha3Code")
    >>> # returns pd.Series(["ZWE", "ITA"])

    All the same options apply to the `resolve` method as well, including from_type, not_found, multiple_candidates,
    and custom_mapping.

    The filter method can be used to filter places for values in a specified format. For example,
    >>> resolver.filter_places(["Zimbabwe", "Italy"], filters={"region": "Africa"})
    >>> # returns ["Zimbabwe"]

    *Note the above example only works if the default concordance table is set.

    Additional methods and properties available on the class include:
        - `concordance_table`: The concordance table used by the class.
        - add_custom_disambiguation: A method to add custom disambiguation rules to the class.
        - get_concordance_dict : A method to get the concordance dictionary for a given from_type and to_type.

    """

    # Shared class-level concordance table (loaded once).
    _CONCORDANCE_TABLE = read_default_concordance_table()

    # Shared class-level disambiguation rules
    # These are edge cases specific to working with countries based on the M49 list of countries and the current
    # functionality of the Data Commons Node endpoint.
    _EDGE_CASES = {
        "congo": "country/COG",
        "france": "country/FRA",
        "caboverde": "country/CPV",
        "antarctica": "antarctica",
        "alandislands": "nuts/FI2",
        "aland": "nuts/FI2",
        "pitcairn": "country/PCN",
        # Svalbard and Jan Mayen Islands
        "svalbardandjanmayenislands": "country/SJM",
        "svalbardjanmayenislands": "country/SJM",
        "svalbardandjanmayenis": "country/SJM",
        "svalbardjanmayenis": "country/SJM",
        "palestine": "country/PSE",
        "saintmartin": "country/MAF",
        # South Georgia and the South Sandwich Islands
        "southgeorgiaandsouthsandwichis": "country/SGS",
        "southgeorgiasouthsandwichis": "country/SGS",
        "sthelena": "country/SHN",
    }

    def __init__(
        self,
        concordance_table: Optional[None | pd.DataFrame | Literal["default"]] = None,
        custom_disambiguation: Optional[dict | Literal["default"]] = None,
        dc_entity_type: Optional[str] = None,
        *,
        dc_api_settings: Optional[dict] = None,
    ):

        # set the Data Commons client
        if dc_api_settings:
            self._dc_client = DataCommonsClient(**dc_api_settings)
        else:
            self._dc_client = DataCommonsClient(dc_instance="datacommons.one.org")

        # set the concordance table
        # if the concordance table is a string and is "default", then use the default concordance table
        if isinstance(concordance_table, str):
            if concordance_table == "default":
                self._concordance_table = self._CONCORDANCE_TABLE
            else:
                raise ValueError(
                    f"Invalid value for concordance_table: {concordance_table}. Must be 'default' or a pandas DataFrame"
                )
        else:
            self._concordance_table = concordance_table

        # validate the concordance table
        if self._concordance_table is not None:
            validate_concordance_table(self._concordance_table)

        self._dc_entity_type = dc_entity_type  # set the Data Commons entity type

        # set any custom disambiguation rules
        if custom_disambiguation == "default":
            self._custom_disambiguation = self._EDGE_CASES
        else:
            self._custom_disambiguation = custom_disambiguation

    def _map_candidates_to_dc_property(
        self, candidates: dict[str, str | list | None], dc_property: str
    ) -> dict[str, str | list | None]:
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
            v
            for val in candidates.values()
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

    def _resolve_with_disambiguation(
        self,
        to_type: str,
        places_to_map: list[str],
        *,
        not_found: Literal["raise", "ignore"] | str = "raise",
    ) -> dict[str, str | list | None]:
        """Disambiguate places then map them to ``to_type``.

        This method uses the Data Commons API and/or any custom disambiguation rules
        to disambiguate places, then concords them to the desired type.

        Args:
            to_type: The desired type to map the places to.
            places_to_map: A list of places to map.
            not_found: Behaviour when a place cannot be disambiguated.

        Returns:
            Mapping of the original places to the resolved values.
        """

        dcid_map = resolve_places_to_dcids(
            dc_client=self._dc_client,
            entities=places_to_map,
            entity_type=self._dc_entity_type,
            disambiguation_dict=self._custom_disambiguation,
        )

        if to_type == "dcid":
            return handle_not_founds(candidates=dcid_map, not_found=not_found)

        if (
            self._concordance_table is not None
            and to_type in self._concordance_table.columns
        ):
            candidates = map_candidates(
                concordance_table=self._concordance_table,
                candidates=dcid_map,
                to_type=to_type,
            )
        else:
            candidates = self._map_candidates_to_dc_property(
                candidates=dcid_map,
                dc_property=to_type,
            )

        return handle_not_founds(candidates=candidates, not_found=not_found)

    def _resolve_without_disambiguation(
        self,
        places_to_map: list[str],
        from_type: str,
        to_type: str,
        *,
        not_found: Literal["raise", "ignore"] | str = "raise",
    ) -> dict[str, str | list | None]:
        """Resolve when the original ``from_type`` is known.

        Places are first mapped to ``dcid`` using the concordance table and then
        converted to ``to_type`` either via the concordance table or Data Commons
        Node.
        """

        if from_type != "dcid":
            dcid_map = map_places(
                concordance_table=self._concordance_table,
                places=places_to_map,
                from_type=from_type,
                to_type="dcid",
            )
        else:
            dcid_map = {place: place for place in places_to_map}

        if to_type == "dcid":
            return handle_not_founds(dcid_map, not_found)

        if (
            self._concordance_table is not None
            and to_type in self._concordance_table.columns
        ):
            candidates = map_candidates(
                concordance_table=self._concordance_table,
                candidates=dcid_map,
                to_type=to_type,
            )
        else:
            candidates = self._map_candidates_to_dc_property(
                candidates=dcid_map,
                dc_property=to_type,
            )

        return handle_not_founds(candidates=candidates, not_found=not_found)

    def _resolve(
        self,
        places: list[str],
        from_type: Optional[str] = None,
        to_type: Optional[str] = "dcid",
        not_found: Literal["raise", "ignore"] | str = "raise",
        multiple_candidates: Literal["raise", "first", "last", "ignore"] = "raise",
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
                    - "last": use the last candidate.
                    - "ignore": keep the value as a list.
            custom_mapping: A dictionary of custom mappings to use.

        Returns:
            A dictionary mapping the places to the desired type.


        """

        # remove any custom mapping from the entities to map
        places_to_map = [
            p for p in places if not (custom_mapping and p in custom_mapping)
        ]

        if not places_to_map:
            return custom_mapping

        if not from_type:
            candidates = self._resolve_with_disambiguation(
                to_type=to_type,
                places_to_map=places_to_map,
                not_found=not_found,
            )
        elif from_type and (
            self._concordance_table is None
            or from_type not in self._concordance_table.columns
        ):
            candidates = self._resolve_with_disambiguation(
                to_type=to_type,
                places_to_map=places_to_map,
                not_found=not_found,
            )
        else:
            candidates = self._resolve_without_disambiguation(
                places_to_map=places_to_map,
                from_type=from_type,
                to_type=to_type,
                not_found=not_found,
            )

        # handle multiple candidates
        candidates = handle_multiple_candidates(
            candidates=candidates, multiple_candidates=multiple_candidates
        )

        # if there are any custom mappings, add them to the candidates
        if custom_mapping:
            candidates = candidates | custom_mapping

        return candidates

    def map_places(
        self,
        places: str | list[str] | pd.Series,
        from_type: Optional[str] = None,
        to_type: Optional[str] = "dcid",
        not_found: Literal["raise", "ignore"] | str = "raise",
        multiple_candidates: Literal["raise", "first", "last", "ignore"] = "raise",
        custom_mapping: Optional[dict[str, str]] = None,
        *,
        ignore_nulls: bool = True,
    ) -> dict[str, str | list[str] | None]:
        """Get a dictionary of places to their resolved formats such as: {place: resolved}

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
                    - "last": use the last candidate.
                    - "ignore": keep the value as a list.

            custom_mapping: A dictionary of custom mappings to use. If this is provided, it will
                override any other mappings. Disambiguation and concordance will not be run for those places.
                The keys are the original places and the values are the resolved places.

            ignore_nulls: If ``True`` null values in ``places`` will be ignored and left unresolved.
                A warning is logged when nulls are dropped. If ``False`` and nulls are present,
                a ``ValueError`` is raised.

        Returns:
            A dictionary mapping the places to the desired format.
        """

        if isinstance(places, str):
            places = [places]
        elif isinstance(places, list):
            places = list(dict.fromkeys(places))
        elif isinstance(places, pd.Series):
            places = list(places.unique())
        else:
            raise ValueError(
                f"Invalid type for places: {type(places)}. Must be one of [str, list[str], pd.Series]"
            )

        null_places = [p for p in places if pd.isna(p)]
        if null_places:
            if ignore_nulls:
                logger.warning(
                    "Null values detected and will be ignored when resolving places"
                )
                places = [p for p in places if not pd.isna(p)]
            else:
                raise ValueError("Null values found in places input")

        return self._resolve(
            places=places,
            from_type=from_type,
            to_type=to_type,
            not_found=not_found,
            multiple_candidates=multiple_candidates,
            custom_mapping=custom_mapping,
        )

    def resolve_places(
        self,
        places: str | list[str] | pd.Series,
        from_type: Optional[str] = None,
        to_type: Optional[str] = "dcid",
        not_found: Literal["raise", "ignore"] | str = "raise",
        multiple_candidates: Literal["raise", "first", "last", "ignore"] = "raise",
        custom_mapping: Optional[dict[str, str]] = None,
        *,
        ignore_nulls: bool = True,
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
                    - "last": use the last candidate.
                    - "ignore": keep the value as a list.

            custom_mapping: A dictionary of custom mappings to use. If this is provided, it will
                override any other mappings. Disambiguation and concordance will not be run for those places.
                The keys are the original places and the values are the resolved places.

            ignore_nulls: If ``True`` null values in ``places`` will be ignored and left unresolved as
                the original value. A warning is logged when nulls are dropped. If ``False`` and nulls are present,
                a ``ValueError`` is raised.

        Returns:
            Resolved places in the desired format
        """

        # get a mapping dictionary for the places
        mapper = self.map_places(
            places=places,
            from_type=from_type,
            to_type=to_type,
            not_found=not_found,
            multiple_candidates=multiple_candidates,
            custom_mapping=custom_mapping,
            ignore_nulls=ignore_nulls,
        )

        # convert back to the original format replacing the original places with the resolved places
        if isinstance(places, str):
            return mapper.get(places)

        elif isinstance(places, pd.Series):
            resolved_list = [p if pd.isna(p) else mapper.get(p) for p in places]
            return pd.Series(resolved_list, index=places.index)

        else:
            result = []
            for p in places:
                if pd.isna(p):
                    if ignore_nulls:
                        result.append(p)
                    else:
                        raise ValueError("Null values found in places input")
                else:
                    result.append(mapper.get(p))
            return result

    @property
    def concordance_table(self) -> pd.DataFrame:
        """Get the concordance table"""

        # raise an error if there is no concordance table set
        if self._concordance_table is None:
            raise ValueError("No concordance table is defined for this resolver.")

        return self._concordance_table

    @classmethod
    def from_concordance_csv(
        cls, concordance_csv_path: str | PathLike, *args, **kwargs
    ) -> "PlaceResolver":
        """Create a PlaceResolver instance using a CSV file for the concordance table.

        Args:
            concordance_csv_path: Path to the CSV file containing the concordance table.
            *args: Additional arguments to pass to the constructor.
            **kwargs: Additional keyword arguments to pass to the constructor.

        Returns:
            PlaceResolver: An instance of PlaceResolver with the specified concordance table.
        """
        concordance_table = pd.read_csv(concordance_csv_path)

        return cls(
            concordance_table=concordance_table,
            *args,
            **kwargs,
        )

    def filter_places(
        self,
        places: list[str] | pd.Series,
        filters: dict[str, str | list[str] | bool],
        from_type: Optional[str] = None,
        not_found: Literal["raise", "ignore"] = "raise",
        multiple_candidates: Literal["raise", "first", "last", "ignore"] = "raise",
    ) -> list[str] | pd.Series:
        """Filter places using one or more categories.

        This method applies multiple filters in sequence and returns the places
        that satisfy all of them.

        Args:
            places: Places to filter.
            filters: Mapping of filter categories to the values to match. Each
                value may be a string or list of strings, or a boolean value.
            from_type: Original format of ``places``. If ``None`` the places are
                automatically disambiguated.
            not_found: How to handle places that cannot be resolved.
            multiple_candidates: How to handle places that resolve to multiple
                candidates.

        Returns:
            The filtered places in the same type as ``places``.
        """

        # normalise filter values
        normalised: dict[str, list[str]] = {}
        for cat, vals in filters.items():
            if isinstance(vals, list):
                normalised[cat] = vals
            else:
                normalised[cat] = [vals]

        # deduplicate places for resolution
        if isinstance(places, list):
            places_unique = list(dict.fromkeys(places))
        elif isinstance(places, pd.Series):
            places_unique = list(places.unique())
        else:
            raise ValueError(
                f"Invalid type for places: {type(places)}. Must be one of [str, list[str], pd.Series]"
            )

        dcid_map = self.map_places(
            places=places_unique,
            from_type=from_type,
            to_type="dcid",
            not_found=not_found,
            multiple_candidates=multiple_candidates,
        )

        result = places_unique
        for category, values in normalised.items():
            cat_map = self.get_concordance_dict("dcid", category, include_nulls=True)
            filtered = []
            for place in result:
                dcid = dcid_map.get(place)
                if isinstance(dcid, list) or dcid is None:
                    continue
                if cat_map.get(dcid) in values:
                    filtered.append(place)
            result = filtered

        if isinstance(places, list):
            return [p for p in places if p in result]

        return pd.Series([p for p in places if p in result])

    def get_concordance_dict(
        self, from_type: str, to_type: str, include_nulls: bool = False
    ) -> dict[str, str | None]:
        """Get a mapping dictionary for a given from_type and to_type from the concordance table.

        Args:
            from_type: The original format of the places.
            to_type: The desired format to convert the places to.
            include_nulls: Whether to include null values in the mapping. Default is False.

        Returns:
            A dictionary mapping the from_type values to the to_type values.
        """

        # if no concordance table is set, raise an error
        if self._concordance_table is None:
            raise ValueError("No concordance table is defined for this resolver.")

        if from_type == to_type:
            logger.warning(
                "from_type and to_type are the same. Returning identical mapping."
            )
            d = {v: v for v in self._concordance_table[from_type].dropna().unique()}

        else:
            raw_dict = self._concordance_table.set_index(from_type)[to_type].to_dict()
            d = {k: v for k, v in raw_dict.items()}

        # if include_nulls then convert any nan to None
        if include_nulls:
            return {k: v if pd.notna(v) else None for k, v in d.items()}

        # remove nan values
        return {k: v for k, v in d.items() if pd.notna(v)}

    def add_custom_disambiguation(self, custom_disambiguation: dict) -> "PlaceResolver":
        """Add custom disambiguation rules to the resolver.

        Args:
            custom_disambiguation: A dictionary of custom disambiguation rules.
                The keys are the place names and the values are the corresponding DCIDs.

        Returns:
            The updated PlaceResolver instance with the custom disambiguation rules added.
        """

        if self._custom_disambiguation is None:
            self._custom_disambiguation = custom_disambiguation
        else:
            self._custom_disambiguation.update(custom_disambiguation)

        return self
