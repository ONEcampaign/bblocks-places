"""Concordance"""

import pandas as pd
from datacommons_client import DataCommonsClient

from bblocks.places.config import logger
from bblocks.places.utils import clean_string


def validate_concordance_table(concordance_table: pd.DataFrame) -> None:
    """Validate the concordance table to ensure it has
    - the required column "dcid"
    - at least one row
    - at least two columns of which one is "dcid"
    - no null values in "dcid"
    - unique values in "dcid"
    """

    # Check if the concordance table has the required column "dcid"
    if "dcid" not in concordance_table.columns:
        raise ValueError(f"Concordance table must have a column named 'dcid'")

    if concordance_table.shape[0] == 0:
        raise ValueError("concordance table must have at least one row")

    if concordance_table["dcid"].isnull().any():
        raise ValueError("`dcid` column must not contain null values")

    if concordance_table["dcid"].duplicated().any():
        raise ValueError("`dcid` values must be unique")

    # At least 2 columns are required
    if len(concordance_table.columns) < 2:
        raise ValueError(f"Concordance table must have at least 2 columns")


def get_concordance_dict(
    concordance_table: pd.DataFrame, from_type: str, to_type: str
) -> dict[str, str]:
    """Return a dictionary with the from_type values as keys and the to_type values as values using the concordance table"""

    if from_type == to_type:
        logger.warning(
            "from_type and to_type are the same. Returning identical mapping."
        )
        return {
            clean_string(v): v for v in concordance_table[from_type].dropna().unique()
        }

    raw_dict = concordance_table.set_index(from_type)[to_type].dropna().to_dict()
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


def map_places(
    concordance_table: pd.DataFrame, places: list[str], from_type, to_type
) -> dict[str, str | None]:
    """Map a list of places to a desired type using the concordance table"""

    concordance_dict = get_concordance_dict(concordance_table, from_type, to_type)

    mapped_series = pd.Series(places, index=places).map(
        lambda x: _map_single_or_list(x, concordance_dict)
    )

    return mapped_series.to_dict()


def map_candidates(
    concordance_table: pd.DataFrame,
    candidates: dict[str, str | list | None],
    to_type: str,
) -> dict[str, str | list | None]:
    """Map a dictionary of candidates as dcids to a desired type using the concordance table"""

    concordance_dict = get_concordance_dict(concordance_table, "dcid", to_type)
    return {
        place: _map_single_or_list(cands, concordance_dict)
        for place, cands in candidates.items()
    }


def fetch_properties(
    dc_client: DataCommonsClient, dcids: list[str], dc_property: str
) -> dict[str, str | list[str] | None]:
    """Fetch a property for a list of DCIDs using the Data Commons node endpoint.

    Args:
        dc_client: An instance of DataCommonsClient.
        dcids: A list of DCIDs to fetch properties for.
        dc_property: The property name to fetch.

    Returns:
        A dictionary mapping each DCID to its property value(s).
    """

    node_response = dc_client.node.fetch_property_values(
        dcids, dc_property
    ).get_properties()
    property_map = {}

    for dcid, nodes in node_response.items():
        if isinstance(nodes, list):
            values = [item.value or item.name or None for item in nodes]
            # Simplify if only one non-null value
            values = [v for v in values if v is not None]
            property_map[dcid] = values[0] if len(values) == 1 else (values or None)
        else:
            property_map[dcid] = nodes.value or nodes.name or None

    return property_map
