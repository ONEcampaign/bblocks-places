"""Concordance"""

import pandas as pd

from bblocks.places.config import logger
from bblocks.places.utils import clean_string


_VALID_SOURCES = [
    "dcid",
    "name_official",
    "name_short",
    "iso2_code",
    "iso3_code",
    "iso_numeric_code",
    "dac_code",
    "m49_code",
]
_VALID_TARGETS = _VALID_SOURCES + [
    "income_level",
    "region",
    "region_code",
    "subregion",
    "subregion_code",
    "intermediate_region",
    "intermediate_region_code",
]


def _check_allowed(source: str, target: str):
    """Check that the source and target are in the allowed sources and targets"""

    if source not in _VALID_SOURCES:
        raise ValueError(
            f"Invalid source: {source}. Allowed sources are {_VALID_SOURCES}"
        )
    if target not in _VALID_TARGETS:
        raise ValueError(
            f"Invalid target: {target}. Allowed targets are {_VALID_TARGETS}"
        )


def get_concordance_dict(
    concordance_table: pd.DataFrame, source: str, target: str
) -> dict[str, str]:
    """Return a dictionary with the source values as keys and the target values as values using the concordance table"""

    _check_allowed(source, target)

    if source == target:
        logger.warning("Source and target are the same. Returning identity mapping.")
        return {
            clean_string(v): v
            for v in concordance_table[source].dropna().unique()
        }

    raw_dict = concordance_table.set_index(source)[target].dropna().to_dict()
    return {clean_string(k): v for k, v in raw_dict.items()}


def _map_single_or_list(val, concordance_dict):
    """Helper function to map a single value or a list of values to their concordance values"""

    if isinstance(val, list):
        mapped = [concordance_dict.get(clean_string(v), None) for v in val]
        mapped = [m for m in mapped if m is not None]
        if not mapped:
            return None
        return mapped[0] if len(mapped) == 1 else mapped
    else:
        return concordance_dict.get(clean_string(val), None)


def map_places(concordance_table: pd.DataFrame, places: list[str], source, target) -> dict[str, str | None]:
    """Map a list of places to a desired type using the concordance table"""

    concordance_dict = get_concordance_dict(concordance_table, source, target)
    return {
        place: _map_single_or_list(place, concordance_dict)
        for place in places
    }


def map_candidates(concordance_table: pd.DataFrame, candidates: dict[str, str | list | None], target: str) -> dict[str, str | list | None]:
    """Map a dictionary of candidates to a desired type using the concordance table"""

    concordance_dict = get_concordance_dict(concordance_table, "dcid", target)
    return {
        place: _map_single_or_list(cands, concordance_dict)
        for place, cands in candidates.items()
    }