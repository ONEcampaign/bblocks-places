"""The main user facing API for the places package

This module will contain all the convenience functions and wrappers
that a user can access

"""

from bblocks.places.resolver import PlaceResolver
from bblocks.places.config import logger
from typing import Optional, Literal
import pandas as pd

# instantiate a PlaceResolver object specific for countries
_country_resolver = PlaceResolver(
    concordance_table="default",
    custom_disambiguation="default",
    dc_entity_type="Country",
)


def get_default_concordance_table() -> pd.DataFrame:
    """Get the default concordance table.

    Returns:
        The default concordance table as a pandas DataFrame.
    """

    return _country_resolver.concordance_table


_VALID_SOURCES = [
    "dcid",
    "name_official",
    "name_short",
    "iso3_code",
    "iso2_code",
    "iso_numeric_code",
    "m49_code",
    "dac_code",
]

_VALID_TARGETS = [
    "region",
    "region_code",
    "subregion",
    "subregion_code",
    "intermediate_region_code",
    "intermediate_region",
    "income_level",
]

_VALID_CONCORDANCE_FIELDS = _country_resolver.concordance_table.columns.tolist()


def _validate_place_format(place_format: str) -> None:
    """Validate the place format, ensuring it is one of the valid formats defined in _VALID_SOURCES.

    Args:
        place_format: the string for the place format to validate.

    Raises:
        ValueError: if the place format is not one of the valid formats.

    """

    if place_format not in _VALID_SOURCES:
        raise ValueError(
            f"Invalid place format: {place_format}. Must be one of {_VALID_SOURCES}."
        )


def _validate_place_target(target_field: str) -> None:
    """Validate the target field, ensuring it is one of the valid formats defined in _VALID_TARGETS.

    Args:
        target_field: the string for the target field to validate.

    Raises:
        ValueError: if the target field is not one of the valid formats.

    """

    if target_field not in _VALID_TARGETS:
        raise ValueError(
            f"Invalid place format: {target_field}. Must be one of {_VALID_TARGETS}."
        )


def _validate_filter_values(filter_category, filter_values: str | list[str]) -> None:
    """Validate the filter values ensuring they are available for the filter category."""

    valid_values = list(
        _country_resolver.concordance_table[filter_category].dropna().unique()
    )

    # ensure all the filter values are in the valid_values list
    if not all(v in valid_values for v in filter_values):
        raise ValueError(
            f"Invalid filter values: {filter_values}. Must be one of {valid_values}."
        )


def _get_list_from_bool(target_field, bool_field, raise_if_empty: bool = False):
    """Helper function to get a list of countries from a boolean field.

    Args:
        target_field: The format of the country names to return.
        bool_field: The boolean field to filter by.
        raise_if_empty: Whether to raise a ``ValueError`` if the result is empty.
            If ``False`` a warning is logged and an empty list is returned.
    """

    # validate the target field
    _validate_place_format(target_field)

    countries = _country_resolver.get_concordance_dict(
        from_type=target_field, to_type=bool_field
    )

    # filter only for values that are True
    countries = {k: v for k, v in countries.items() if v is True}

    result = list(countries.keys())

    if not result:
        msg = f"No places found for boolean field '{bool_field}'"
        if raise_if_empty:
            raise ValueError(msg)
        logger.warning(msg)

    return result


def get_un_members(
    place_format: Optional[str] = "dcid", *, raise_if_empty: bool = False
) -> list[str | int]:
    """Get a list of UN members in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".
            Available formats are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code

    Returns:
        A list of country names in the specified format.

    Raises:
        ValueError: If ``raise_if_empty`` is ``True`` and no countries are found.
    """

    return _get_list_from_bool(place_format, "un_member", raise_if_empty=raise_if_empty)


def get_un_observers(
    place_format: Optional[str] = "dcid", *, raise_if_empty: bool = False
) -> list[str | int]:
    """Get a list of UN observers in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".
            Available formats are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code

    Returns:
        A list of country names in the specified format.

    Raises:
        ValueError: If ``raise_if_empty`` is ``True`` and no countries are found.
    """

    return _get_list_from_bool(place_format, "un_observer", raise_if_empty=raise_if_empty)


def get_m49_places(
    place_format: Optional[str] = "dcid", *, raise_if_empty: bool = False
) -> list[str | int]:
    """Get a list of M49 countries and areas in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".
            Available formats are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code

    Returns:
        A list of country names in the specified format.

    Raises:
        ValueError: If ``raise_if_empty`` is ``True`` and no countries are found.
    """

    return _get_list_from_bool(place_format, "m49_member", raise_if_empty=raise_if_empty)


def get_sids(
    place_format: Optional[str] = "dcid", *, raise_if_empty: bool = False
) -> list[str | int]:
    """Get a list of Small Island Developing States (SIDS) in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".
            Available formats are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code

    Returns:
        A list of country names in the specified format.

    Raises:
        ValueError: If ``raise_if_empty`` is ``True`` and no countries are found.
    """

    return _get_list_from_bool(place_format, "sids", raise_if_empty=raise_if_empty)


def get_ldc(
    place_format: Optional[str] = "dcid", *, raise_if_empty: bool = False
) -> list[str | int]:
    """Get a list of Least Developed Countries (LDC) in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".
            Available formats are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code

    Returns:
        A list of country names in the specified format.

    Raises:
        ValueError: If ``raise_if_empty`` is ``True`` and no countries are found.
    """

    return _get_list_from_bool(place_format, "ldc", raise_if_empty=raise_if_empty)


def get_lldc(
    place_format: Optional[str] = "dcid", *, raise_if_empty: bool = False
) -> list[str | int]:
    """Get a list of Landlocked Developing Countries (LLDC) in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".
            Available formats are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code

    Returns:
        A list of country names in the specified format.

    Raises:
        ValueError: If ``raise_if_empty`` is ``True`` and no countries are found.
    """

    return _get_list_from_bool(place_format, "lldc", raise_if_empty=raise_if_empty)


def resolve(
    places: str | list[str] | pd.Series,
    from_type: Optional[str] = None,
    to_type: Optional[str] = "dcid",
    not_found: Literal["raise", "ignore"] | str = "raise",
    multiple_candidates: Literal["raise", "first", "last", "ignore"] = "raise",
    custom_mapping: Optional[dict] = None,
):
    """Resolve places

    Resolve places to a desired format. This function disambiguates places
    if disambiguation is needed, and map them to the desired format, replacing
    the original places with the resolved ones.

    Args:
        places: The places to resolve. This can be a string, a list of strings, or a pandas Series.

        to_type: The format to resolve the places to. Defaults to "dcid".
            Options are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code
            - region
            - region_code
            - subregion
            - subregion_code
            - intermediate_region_code
            - intermediate_region
            - income_level
            - Any other valid property in Data Commons

        from_type: The format of the input places. If not provided, the places will be
            disambiguated automatically. Defaults to None.
            Options are:
            - "dcid"
            - "name_official"
            - "name_short"
            - "iso3_code"
            - "iso2_code"
            - "iso_numeric_code"
            - "m49_code"
            - "dac_code"

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

    Returns:
        Resolved places
    """

    # check if the from_type is valid
    if from_type is not None:
        _validate_place_format(from_type)

    return _country_resolver.resolve(
        places=places,
        to_type=to_type,
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
        custom_mapping=custom_mapping,
    )


def resolve_map(
    places: str | list[str] | pd.Series,
    to_type: Optional[str] = "dcid",
    from_type: Optional[str] = None,
    not_found: Literal["raise", "ignore"] | str = "raise",
    multiple_candidates: Literal["raise", "first", "last", "ignore"] = "raise",
    custom_mapping: Optional[dict] = None,
) -> dict[str, str | int | None | list]:
    """Resolve places to a mapping dictionary of {place: resolved}

    Resolve places to a desired format. This function disambiguates places
    if disambiguation is needed, and map them to the desired format, returning a
    dictionary with the original places as keys and the resolved places as values.

    Args:
        places: The places to resolve

        to_type: The desired format to resolve the places to. Defaults to "dcid".
            Options are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code
            - region
            - region_code
            - subregion
            - subregion_code
            - intermediate_region_code
            - intermediate_region
            - income_level
            - Any other valid property in Data Commons

        from_type: The original format of the places. Default is None.
            If None, the places will be disambiguated automatically using Data Commons
            Options are:
            - "dcid"
            - "name_official"
            - "name_short"
            - "iso3_code"
            - "iso2_code"
            - "iso_numeric_code"
            - "m49_code"
            - "dac_code"

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

    Returns:
        A dictionary mapping the places to the desired format.
    """

    # check if the from_type is valid
    if from_type is not None:
        _validate_place_format(from_type)

    return _country_resolver.resolve_map(
        places=places,
        to_type=to_type,
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
        custom_mapping=custom_mapping,
    )


def filter_places(
    places: list[str] | pd.Series,
    filter_category: str,
    filter_values: str | list[str],
    from_type: Optional[str] = None,
    not_found: Literal["raise", "ignore"] = "raise",
    multiple_candidates: Literal["raise", "first", "last"] = "raise",
) -> pd.Series | list:
    """Filter places

    Filter places based on a specific category like "region" for specific values like "Africa".
    This function can disambiguate places if needed, and filter them based on the specified category
    and values.

    Args:
        places: The places to filter

        filter_category: The category to filter the places by. This can be a string or a list of strings.
            Options are:
            - region
            - region_code
            - subregion
            - subregion_code
            - intermediate_region_code
            - intermediate_region
            - income_level

        filter_values: The values to filter the places by. This can be a string or a list of strings.

        from_type:  The original format of the places. Default is None.
            If None, the places will be disambiguated automatically using Data Commons
            Options are:
            - "dcid"
            - "name_official"
            - "name_short"
            - "iso3_code"
            - "iso2_code"
            - "iso_numeric_code"
            - "m49_code"
            - "dac_code"

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

    Returns:
        Filtered places
    """

    # check if the from_type is valid
    if from_type is not None:
        _validate_place_format(from_type)

    # check if the filter_category is valid
    _validate_place_target(filter_category)

    # check if the filter_values are valid - should exist in the concordance table
    if isinstance(filter_values, str):
        filter_values = [filter_values]

    _validate_filter_values(filter_category, filter_values)

    return _country_resolver.filter(
        places=places,
        filter_category=filter_category,
        filter_values=filter_values,
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
    )


def filter_african_countries(
    places: str | list[str] | pd.Series,
    from_type: Optional[str] = None,
    not_found: Literal["raise", "ignore"] = "raise",
    multiple_candidates: Literal["raise", "first", "last"] = "raise",
):
    """Filter places for African countries

    Filter places based on the region "Africa". This function can disambiguate places
    if needed, then filter them.

    Args:
        places: The places to filter

        from_type:  The original format of the places. Default is None.
            If None, the places will be disambiguated automatically using Data Commons
            Options are:
            - "dcid"
            - "name_official"
            - "name_short"
            - "iso3_code"
            - "iso2_code"
            - "iso_numeric_code"
            - "m49_code"
            - "dac_code"

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
    """

    return filter_places(
        places=places,
        filter_category="region",
        filter_values="Africa",
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
    )


def get_places_by_multiple(
    filters: dict[str, str | list[str | int | bool]],
    place_format: str = "dcid",
    *,
    raise_if_empty: bool = False,
) -> list[str | int]:
    """Get places based on multiple filters.


    This function can be used to get all places based on multiple filters for multiple categories and values,
    for example, by region and income level for values like "Africa" and "High income".

    Args:
        filters: A dictionary of filters to apply. The keys are the categories to filter by and the values are the
            values to filter by. The values can be a string or a list of strings.
            Example: {"region": "Africa","income_level": ["High income", "Upper middle income"]}

        place_format: The format of the country names to return. Defaults to "dcid".
            Available formats are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code

    Returns:
        A list of place names in the specified format.

    Raises:
        ValueError: If ``raise_if_empty`` is ``True`` and no places match
        the provided filters.

    """

    # check if the filter_dict is valid
    _validate_place_format(place_format)

    for key, value in filters.items():
        # if the value is not already a list, wrap it in a list
        if not isinstance(value, list):
            value = [value]
            filters[key] = value  # update dict for later use

        # validate each value
        _validate_filter_values(key, value)

    # filter the concordance table based on the filter
    result = list(
        _country_resolver.concordance_table.query(
            " and ".join([f"{key} in {value}" for key, value in filters.items()])
        )[place_format]
        .dropna()
        .unique()
    )

    if not result:
        msg = f"No places found for filters {filters}"
        if raise_if_empty:
            raise ValueError(msg)
        logger.warning(msg)

    return result


def get_places_by(
    by: str,
    filter_values: str | list[str],
    place_format: Optional[str] = "dcid",
    *,
    raise_if_empty: bool = False,
) -> list[str | int]:
    """Get places based on a specific category and values.

    This function can be used to get places based on a specific category like "region" for specific values like "Africa".

    Args:
        by: The category to filter the places by. This can be a string or a list of strings.
            Options are:
            - region
            - region_code
            - subregion
            - subregion_code
            - intermediate_region_code
            - intermediate_region
            - income_level

        filter_values: The values to filter the places by. This can be a string or a list of strings.

        place_format: The format of the country names to return. Defaults to "dcid".
            Available formats are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code
        raise_if_empty: Whether to raise a ``ValueError`` if no places match the
            criteria. If ``False`` a warning is logged and an empty list is returned.

    """

    # check if the by is valid
    _validate_place_target(by)

    if isinstance(filter_values, str):
        filter_values = [filter_values]

    # check if the filter_values are valid - should exist in the concordance table
    _validate_filter_values(by, filter_values)

    # check if the place_format is valid
    _validate_place_format(place_format)

    # filter the concordance table
    mapper = _country_resolver.get_concordance_dict(from_type=place_format, to_type=by)
    result = [k for k, v in mapper.items() if v in filter_values]

    if not result:
        msg = f"No places found for {by} in {filter_values}"
        if raise_if_empty:
            raise ValueError(msg)
        logger.warning(msg)

    return result


def get_african_countries(
    place_format: Optional[str] = "dcid",
    exclude_non_un_members: Optional[bool] = True,
    *,
    raise_if_empty: bool = False,
) -> list[str | int]:
    """Get a list of African countries in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".
            Options are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code
        exclude_non_un_members: Whether to exclude non-UN members. Defaults to True. If set to False, non-UN member
            countries and areas such as Western Sahara will be included in the list.

        raise_if_empty: Whether to raise a ``ValueError`` if no countries are found.
            If ``False`` a warning is logged and an empty list is returned.

    Returns:
        A list of African country names in the specified format.

    Raises:
        ValueError: If ``raise_if_empty`` is ``True`` and no countries are found.
    """

    filter_dict = {"region": "Africa"}

    if exclude_non_un_members:
        filter_dict = {"region": "Africa", "un_member": True}

    return get_places_by_multiple(
        filters=filter_dict,
        place_format=place_format,
        raise_if_empty=raise_if_empty,
    )
