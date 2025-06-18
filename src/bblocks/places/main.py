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

    return _get_list_from_bool(
        place_format, "un_observer", raise_if_empty=raise_if_empty
    )


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

    return _get_list_from_bool(
        place_format, "m49_member", raise_if_empty=raise_if_empty
    )


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


def resolve_places(
    places: str | list[str] | pd.Series,
    from_type: Optional[str] = None,
    to_type: Optional[str] = "dcid",
    not_found: Literal["raise", "ignore"] | str = "raise",
    multiple_candidates: Literal["raise", "first", "last", "ignore"] = "raise",
    custom_mapping: Optional[dict] = None,
    *,
    ignore_nulls: bool = True,
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

        ignore_nulls: If ``True`` null values are ignored during resolution and left as ``None``.
            A warning is logged for ignored values. If ``False`` and nulls are present, a ``ValueError`` is raised.

    Returns:
        Resolved places
    """

    # check if the from_type is valid
    if from_type is not None:
        _validate_place_format(from_type)

    return _country_resolver.resolve_places(
        places=places,
        to_type=to_type,
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
        custom_mapping=custom_mapping,
        ignore_nulls=ignore_nulls,
    )


def map_places(
    places: str | list[str] | pd.Series,
    to_type: Optional[str] = "dcid",
    from_type: Optional[str] = None,
    not_found: Literal["raise", "ignore"] | str = "raise",
    multiple_candidates: Literal["raise", "first", "last", "ignore"] = "raise",
    custom_mapping: Optional[dict] = None,
    *,
    ignore_nulls: bool = True,
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

        ignore_nulls: If ``True`` null values are ignored during resolution and left as ``None``.
            A warning is logged for ignored values. If ``False`` and nulls are present, a ``ValueError`` is raised.

    Returns:
        A dictionary mapping the places to the desired format.
    """

    # check if the from_type is valid
    if from_type is not None:
        _validate_place_format(from_type)

    return _country_resolver.map_places(
        places=places,
        to_type=to_type,
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
        custom_mapping=custom_mapping,
        ignore_nulls=ignore_nulls,
    )


def filter_places(
    places: list[str] | pd.Series,
    filters: dict[str, str | list[str] | bool],
    from_type: Optional[str] = None,
    not_found: Literal["raise", "ignore"] = "raise",
    multiple_candidates: Literal["raise", "first", "last", "ignore"] = "raise",
    *,
    raise_if_empty: bool = False,
) -> pd.Series | list:
    """Filter places using one or more categories.

    This function applies several filters in sequence, returning the places that
    match all the provided criteria.

    Args:
        places: The places to filter.

        filters: A mapping of filter categories to the values to match. Values
            may be a single string or a list of strings or a boolean for
            filters such as `un_member`
            Available filter categories are:
            - region
            - region_code
            - subregion
            - subregion_code
            - intermediate_region_code
            - intermediate_region
            - income_level
            - m49_member: M49 country list member. `True` for M49 countries, `False` for non-M49 countries.
            - ldc: Least Developed Countries. `True` for LDCs, `False` for non-LDCs.
            - lldc: Landlocked Developing Countries. `True` for LLDCs, `False` for non-LLDCs.
            - sids: Small Island Developing States. `True` for SIDS, `False` for non-SIDS.
            - un_member: UN member states. `True` for UN members, `False` for non-UN members.
            - un_observer: UN observer states. `True` for UN observers, `False` for non-UN observers.
            - un_former_member: Former UN member states. `True` for former UN members, `False` for non-former UN members.

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

        raise_if_empty: Whether to raise a ``ValueError`` if the filtered
            result is empty. If ``False`` a warning is logged and an empty list
            is returned.

    Returns:
        The places that satisfy all filters, in the same type as ``places``.

    Raises:
        ValueError: If ``raise_if_empty`` is ``True`` and no places match the
            provided filters.
    """

    if from_type is not None:
        _validate_place_format(from_type)

    for category, values in filters.items():
        # _validate_place_target(category)
        if not isinstance(values, list):
            values = [values]
            filters[category] = values
        _validate_filter_values(category, values)

    result = _country_resolver.filter_places(
        places=places,
        filters=filters,
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
    )

    empty = False
    if isinstance(result, list) and not result:
        empty = True
    elif isinstance(result, pd.Series) and result.empty:
        empty = True

    if empty:
        msg = f"No places found for filters {filters}"
        if raise_if_empty:
            raise ValueError(msg)
        logger.warning(msg)

    return result


def filter_african_countries(
    places: str | list[str] | pd.Series,
    exclude_non_un_members: Optional[bool] = True,
    from_type: Optional[str] = None,
    not_found: Literal["raise", "ignore"] = "raise",
    multiple_candidates: Literal["raise", "first", "last", "ignore"] = "raise",
    *,
    raise_if_empty: bool = False,
):
    """Filter places for African countries

    Filter places based on the region "Africa". This function can disambiguate places
    if needed, then filter them.

    Args:
        places: The places to filter

        exclude_non_un_members: Whether to exclude non-UN members. Defaults to True. If set to False, non-UN member
            countries and areas such as Western Sahara will be included in the list.

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
        raise_if_empty: Whether to raise a ``ValueError`` if the filtered
            result is empty. If ``False`` a warning is logged and an empty list
            is returned.
    """

    filters = (
        {"region": "Africa", "un_member": True}
        if exclude_non_un_members
        else {"region": "Africa"}
    )

    return filter_places(
        places=places,
        filters=filters,
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
        raise_if_empty=raise_if_empty,
    )


def get_places(
    filters: dict[str, str | list[str | int | bool]],
    place_format: str = "dcid",
    *,
    raise_if_empty: bool = False,
) -> list[str | int]:
    """Get places based on one or more filters.

    This function can be used to get all places that match a set of filters, for
    example by region and income level.

    Args:
        filters: A dictionary of filters to apply. The keys are the categories to filter by
            and the values are the values to filter for. Each value can be a string
            or a list of strings. Example: ``{"region": "Africa", "income_level": ["High income"]}``
            Available categories are:
            - region
            - region_code
            - subregion
            - subregion_code
            - intermediate_region_code
            - intermediate_region
            - income_level
            - m49_member
            - ldc
            - lldc
            - sids
            - un_member
            - un_observer
            - un_former_member

        place_format: place_format: The format of the country names to return. Defaults to "dcid".
            Options are:
            - dcid
            - name_official
            - name_short
            - iso3_code
            - iso2_code
            - iso_numeric_code
            - m49_code
            - dac_code

        raise_if_empty: Whether to raise a ``ValueError`` if no places match the filters.

    Returns:
        A list of place names in the specified format.

    Raises:
        ValueError: If ``raise_if_empty`` is ``True`` and no places match the provided filters.
    """

    _validate_place_format(place_format)

    for key, value in filters.items():
        if not isinstance(value, list):
            value = [value]
            filters[key] = value
        _validate_filter_values(key, value)

    query = " and ".join([f"{k} in {v}" for k, v in filters.items()])
    result = list(
        _country_resolver.concordance_table.query(query)[place_format].dropna().unique()
    )

    if not result:
        msg = f"No places found for filters {filters}"
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

    return get_places(
        filters=filter_dict,
        place_format=place_format,
        raise_if_empty=raise_if_empty,
    )
