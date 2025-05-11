"""Disambiguator"""

from datacommons_client import DataCommonsClient
from typing import Optional

from bblocks.places.utils import clean_string, split_list


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


def fetch_dcids_by_name(
    dc_client: DataCommonsClient,
    entities: str | list,
    entity_type: str,
    chunk_size: Optional[int] = 30,
) -> dict[str, str | list | None]:
    """Fetch DCIDs for a list of entities using the DataCommonsClient.

    Args:
        dc_client: An instance of DataCommonsClient.
        entities: A single entity name or a list of entity names.
        entity_type: The type of the entity (e.g., "Country"). It must be a valid Data Commons type.
        chunk_size: The size of each chunk to split the list into. If None, no chunking is done.

    Returns:
        A dictionary mapping entity names to their corresponding DCIDs. If an entity name is not found, it will be mapped to None.
    """

    if not chunk_size:
        dcids = dc_client.resolve.fetch_dcids_by_name(
            entities, entity_type
        ).to_flat_dict()

    else:
        dcids = {}
        for chunk in split_list(entities, chunk_size):
            chunk_dcids = dc_client.resolve.fetch_dcids_by_name(
                chunk, entity_type
            ).to_flat_dict()
            dcids.update(chunk_dcids)

    # replace empty lists with None
    for k, v in dcids.items():
        # if v is an empty list, replace it with None
        if isinstance(v, list) and len(v) == 0:
            dcids[k] = None

    return dcids


def custom_disambiguation(entity: str) -> str | None:
    """Disambiguate a given entity name using special cases.

    Args:
        entity: The entity name to disambiguate.

    Returns:
        The disambiguated DCID if found in special cases, otherwise None.
    """

    cleaned_string = clean_string(entity)
    if cleaned_string in _EDGE_CASES:
        return _EDGE_CASES[cleaned_string]
    return None


def disambiguation_pipeline(
    dc_client: DataCommonsClient,
    entities: str | list[str],
    entity_type: Optional[str],
    chunk_size: Optional[int] = 30,
) -> dict[str, str | list | None]:
    """Disambiguate entities to their DCIDs

    This function takes ambiguous entity names and resolves them to their corresponding DCIDs using the DataCommonsClient and
    custom disambiguation rules for edge cases.

    Args:
        dc_client: An instance of DataCommonsClient.
        entities: A single entity name or a list of entity names.
        entity_type: The type of the entity (e.g., "Country"). It must be a valid Data Commons type.
        chunk_size: The size of each chunk to split the list into. If None, no chunking is done.

    Returns:
        A dictionary mapping entity names to their corresponding DCIDs. If an entity name is not found, it will be mapped to None.
    """

    resolved_entities = {}
    entities_to_disambiguate = []

    # loop through the entities checking for edge cases
    for entity in entities:
        # if the entity is an edge case, add the dcid to the dictionary and remove the entity from the list
        dcid = custom_disambiguation(entity)
        if dcid is not None:
            resolved_entities[entity] = dcid
        else:
            # if the entity is not an edge case, add it to the list of entities to disambiguate
            entities_to_disambiguate.append(entity)

    # if there are still entities left, fetch the dcids from the datacommons client
    if entities_to_disambiguate:
        # fetch the dcids from the datacommons client
        dcids = fetch_dcids_by_name(
            dc_client, entities_to_disambiguate, entity_type, chunk_size
        )
        resolved_entities.update(dcids)

    return resolved_entities
