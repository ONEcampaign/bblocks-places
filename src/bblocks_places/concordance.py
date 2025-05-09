"""Concordance"""

import pandas as pd

from bblocks_places.config import Paths, logger


_VAIID_SOURCES = [
    "dcid",
    "name",
    "iso2_code",
    "iso3_code",
    "name_short",
]  # TODO: Add more sources
_VALID_TARGETS = _VAIID_SOURCES + ["income_level"]  # TODO: Add more targets


def _check_allowed(source: str, target: str):
    """Check that the source and target are in the allowed sources and targets"""

    if source not in _VAIID_SOURCES:
        raise ValueError(
            f"Invalid source: {source}. Allowed sources are {_VAIID_SOURCES}"
        )
    if target not in _VALID_TARGETS:
        raise ValueError(
            f"Invalid target: {target}. Allowed targets are {_VALID_TARGETS}"
        )


def get_concordance_dict(concordance_table: pd.DataFrame, source: str, target: str) -> dict[str, str]:
    """Return a dictionary with the source values as keys and the target values as values using the concordance table"""

    # Check that the source and target are in the allowed sources and targets
    _check_allowed(source, target)

    # check if the source and target are the same
    if source == target:
        logger.warn(f"Source and target are the same")

    # return a dictionary with the source values as keys and the target values as values using the concordance table
    return (
        concordance_table
        # create new columns for the source and target to avoid errors where the source and target are the same
        .assign(source=source, target=target)
        .set_index(source)[target]
        .to_dict()
    )


def map_places(concordance_table: pd.dataFrame, places: list[str], source, target) -> dict[str, str | None]:
    """Map a list of places to their concordance values"""

    concordance_dict = get_concordance_dict(concordance_table=concordance_table, source=source, target=target)
    return {place: concordance_dict.get(place, None) for place in places}


def map_candidates(concordance_table: pd.dataFrame,
    candidates: dict[str, str | list | None], target: str
) -> dict[str, str | list | None]:
    """Map a dictionary of candidates to a desired type"""

    concordance_dict = get_concordance_dict(concordance_table=concordance_table, source="dcid", target=target)

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
