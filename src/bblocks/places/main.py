"""The main user facing API for the places package

This module will contain all the convenience functions and wrappers
that a user can access

"""
from bblocks.places.resolver import PlaceResolver
from typing import Optional, Literal
import pandas as pd

# instantiate a PlaceResolver object specific for countries
_country_resolver = PlaceResolver(concordance_table="default",
                                  custom_disambiguation="default",
                                  dc_entity_type="Country")

_valid_sources = [
    "dcid",
    "name_official",
    "name_short",
    "iso3_code",
    "iso2_code",
    "iso_numeric_code",
    "m49_code",
    "dac_code",
]

_valid_targets = _valid_sources + ["region",
                                   "region_code",
                                   "subregion",
                                   "subregion_code",
                                   "intermediate_region_code",
                                   "intermediate_region",
                                   "income_level"

]


def _get_list_from_bool(target_field, bool_field):
    """ """

    if target_field not in _valid_sources:
        raise ValueError(f"Invalid place format: {target_field}. Must be one of {_valid_sources}.")

    countries = _country_resolver.get_concordance_dict(from_type=target_field, to_type=bool_field)

    # filter only for value that are True
    countries = {k: v for k, v in countries.items() if v is True}

    # return the keys of the dictionary
    return list(countries.keys())


def get_un_members(place_format: Optional[str] = "dcid") -> list[str | int]:
    """Get a list of UN members in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".
        TODO: Add the available formats here.

    Returns:
        A list of country names in the specified format.
    """

    return _get_list_from_bool(place_format, "un_member")

def get_un_observers(place_format: Optional[str] = "dcid") -> list[str | int]:
    """Get a list of UN observers in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".
            TODO: Add the available formats here.

    Returns:
        A list of country names in the specified format.
    """

    return _get_list_from_bool(place_format, "un_observer")

def get_m49_places(place_format: Optional[str] = "dcid") -> list[str | int]:
    """Get a list of M49 countries and areas in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".

    Returns:
        A list of country names in the specified format.
    """

    return _get_list_from_bool(place_format, "m49_member")


def get_sids(place_format: Optional[str] = "dcid") -> list[str | int]:
    """Get a list of Small Island Developing States (SIDS) in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".

    Returns:
        A list of country names in the specified format.
    """

    return _get_list_from_bool(place_format, "sids")

def get_ldc(place_format: Optional[str] = "dcid") -> list[str | int]:
    """Get a list of Least Developed Countries (LDC) in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".

    Returns:
        A list of country names in the specified format.
    """

    return _get_list_from_bool(place_format, "ldc")

def get_lldc(place_format: Optional[str] = "dcid") -> list[str | int]:
    """Get a list of Landlocked Developing Countries (LLDC) in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".

    Returns:
        A list of country names in the specified format.
    """

    return _get_list_from_bool(place_format, "lldc")


def resolve_places(places: str | list[str] | pd.Series,
            to_type: Optional[str] = "dcid",
            from_type: Optional[str] = None,
            not_found: Literal["raise", "ignore"] | str = "raise",
            multiple_candidates: Literal["raise", "first", "ignore"] = "raise",
            custom_mapping: Optional[dict] = None,
            ):
    """ """

    # check if the to_type is valid
    if to_type not in _valid_targets:
        raise ValueError(f"Invalid country format: {to_type}. Must be one of {_valid_targets}.")

    # check if the from_type is valid
    if from_type is not None and from_type not in _valid_sources:
        raise ValueError(f"Invalid country format: {from_type}. Must be one of {_valid_sources}.")

    return _country_resolver.resolve(
        places=places,
        to_type=to_type,
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
        custom_mapping=custom_mapping,
    )

def resolve_places_mapping(places: str | list[str] | pd.Series,
                            to_type: Optional[str] = "dcid",
                            from_type: Optional[str] = None,
                            not_found: Literal["raise", "ignore"] | str = "raise",
                            multiple_candidates: Literal["raise", "first", "ignore"] = "raise",
                            custom_mapping: Optional[dict] = None,
                            ) -> dict[str, str | int | None | list]:
    """ """

    # check if the to_type is valid
    if to_type not in _valid_targets:
        raise ValueError(f"Invalid country format: {to_type}. Must be one of {_valid_targets}.")
    # check if the from_type is valid
    if from_type is not None and from_type not in _valid_sources:
        raise ValueError(f"Invalid country format: {from_type}. Must be one of {_valid_sources}.")

    return _country_resolver.resolve_map(
        places=places,
        to_type=to_type,
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
        custom_mapping=custom_mapping,
    )


def filter_places(places: str | list[str] | pd.Series,
           filter_type: str,
           filter_values: str | list[str],
           from_type: Optional[str] = None,
           not_found: Literal["raise", "ignore"] = "raise",
           multiple_candidates: Literal["raise", "first"] = "raise",
            ):
    """ """

    # check if the filter_type is valid
    if filter_type not in _valid_targets:
        raise ValueError(f"Invalid country format: {filter_type}. Must be one of {_valid_targets}.")

    # check if the from_type is valid
    if from_type is not None and from_type not in _valid_sources:
        raise ValueError(f"Invalid country format: {from_type}. Must be one of {_valid_sources}.")

    # check if the filter_values are valid - should exist in the concordance table
    if isinstance(filter_values, str):
        filter_values = [filter_values]
    if not all([v in _country_resolver.concordance_table[filter_type].values for v in filter_values]):
        # get a list of valid values, excluding any nulls
        valid_values = list(_country_resolver.concordance_table[filter_type].dropna().unique())
        raise ValueError(f"Invalid filter values: {filter_values}. Must be one of {valid_values}.")


    return _country_resolver.filter(
        places=places,
        filter_type=filter_type,
        filter_values=filter_values,
        from_type=from_type,
        not_found=not_found,
        multiple_candidates=multiple_candidates,
    )

def filter_african_countries(places: str | list[str] | pd.Series,
                             from_type: Optional[str] = None,
                             not_found: Literal["raise", "ignore"] = "raise",
                             multiple_candidates: Literal["raise", "first"] = "raise"):
    """Filter a list of places to only include African countries.
    """
    return filter_places(places=places,
                         filter_type="region",
                         filter_values="Africa",
                         from_type=from_type,
                         not_found=not_found,
                         multiple_candidates=multiple_candidates)



def get_places_by(by: str, filter_values: str | list[str], place_format: Optional[str] = "dcid") -> list[str | int]:
    """ """

    # check if the by is valid
    if by not in _valid_targets:
        raise ValueError(f"Invalid country format: {by}. Must be one of {_valid_targets}.")

    if isinstance(filter_values, str):
        filter_values = [filter_values]

    # check if the filter_values are valid - should exist in the concordance table
    if not all([v in _country_resolver.concordance_table[by].values for v in filter_values]):
        # get a list of valid values, excluding any nulls
        valid_values = list(_country_resolver.concordance_table[by].dropna().unique())
        raise ValueError(f"Invalid filter values: {filter_values}. Must be one of {valid_values}.")

    # check if the place_format is valid
    if place_format not in _valid_sources:
        raise ValueError(f"Invalid country format: {place_format}. Must be one of {_valid_sources}.")

    # filter the concordance table
    mapper = _country_resolver.get_concordance_dict(from_type=place_format, to_type=by)
    return [k for k, v in mapper.items() if v in filter_values]


def get_african_countries(place_format: Optional[str] = "dcid") -> list[str | int]:
    """Get a list of African countries in the specified format.

    Args:
        place_format: The format of the country names to return. Defaults to "dcid".

    Returns:
        A list of country names in the specified format.
    """

    return get_places_by("region", "Africa", place_format)

