from typing import Any, TypeAlias

from bblocks_places.config import NotFoundBehavior, MultipleCandidatesBehavior, logger
from bblocks_places.utils import map_dict

Name: TypeAlias = str
DCID: TypeAlias = str
NameToDCIDs: TypeAlias = dict[Name, list[DCID]]
DCIDToProps: TypeAlias = dict[DCID, Any]


def map_dcids_to_props(
    name_to_dcids: NameToDCIDs, dcid_to_props: DCIDToProps
) -> dict[Name, list[Any]] | None:
    """Map DCIDs to their properties."""
    return map_dict(name_to_dcids, dcid_to_props)


def _handle_not_found(
    name: str,
    to: str,
    behavior: NotFoundBehavior | str,
) -> Any | None:
    match behavior:
        case NotFoundBehavior.RAISE:
            raise ValueError(f"Could not find a '{to}' match for: {name}")
        case NotFoundBehavior.IGNORE:
            logger.warn(f"Could not find a '{to}' match for: {name}. Returning None.")
            return None
        case _:
            logger.warn(
                f"Could not find a '{to}' match for: {name}. Returning '{behavior}'."
            )
            return behavior


def _handle_multiple_as_first(
    name: str,
    to: str,
    behavior: MultipleCandidatesBehavior,
) -> bool:
    match behavior:
        case MultipleCandidatesBehavior.RAISE:
            raise ValueError(f"Multiple '{to}' matches for: {name}")
        case MultipleCandidatesBehavior.FIRST:
            logger.warn(
                f"Multiple '{to}' matches for: {name}. Returning the first match."
            )
            return True
        case _:
            logger.warn(f"Multiple '{to}' matches for: {name}. Returning all matches.")
            return False


def parse_ambiguous(
    candidates: dict[str, Any],
    to: str,
    not_found: NotFoundBehavior | str = NotFoundBehavior.RAISE,
    multiple: MultipleCandidatesBehavior = MultipleCandidatesBehavior.RAISE,
) -> dict[str, Any]:
    """Parse ambiguous candidates."""

    for name, val in candidates.items():
        if not val:
            candidates[name] = _handle_not_found(name, to, not_found)
            continue
        elif isinstance(val, list) and len(val) > 1:
            candidates[name] = (
                val[0] if _handle_multiple_as_first(name, to, multiple) else val
            )

    return candidates
