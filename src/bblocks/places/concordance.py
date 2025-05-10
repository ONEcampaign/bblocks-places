"""Concordance"""

import pandas as pd

from bblocks.places.config import logger


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

    # Check that the source and target are in the allowed sources and targets
    _check_allowed(source, target)

    # check if the source and target are the same
    if source == target:
        logger.warn(f"Source and target are the same")
        return {v: v for v in concordance_table[source].dropna().unique()}

    return concordance_table.set_index(source)[target].to_dict()


def map_places(
    concordance_table: pd.DataFrame, places: list[str], source, target
) -> dict[str, str | None]:
    """Map a list of places to their concordance values"""

    concordance_dict = get_concordance_dict(
        concordance_table=concordance_table, source=source, target=target
    )
    return {place: concordance_dict.get(place, None) for place in places}


def map_candidates(
    concordance_table: pd.DataFrame,
    candidates: dict[str, str | list | None],
    target: str,
) -> dict[str, str | list | None]:
    """Map a dictionary of candidates to a desired type"""

    concordance_dict = get_concordance_dict(
        concordance_table=concordance_table, source="dcid", target=target
    )

    for place, cands in candidates.items():
        # if the candidate is a single value or None, map it to the target
        if not isinstance(cands, list):
            resolved_place = concordance_dict.get(cands, None)

        # if the candidate is a list, map each value to the target
        else:
            resolved_place = [concordance_dict.get(c, None) for c in cands]
            # remove any Nones from the list
            resolved_place = [r for r in resolved_place if r is not None]

            # if the list is empty, set it to None
            if not resolved_place:
                resolved_place = None

            elif len(resolved_place) == 1:
                # if there is only one value, set it to the value
                resolved_place = resolved_place[0]

        candidates[place] = resolved_place

    return candidates
