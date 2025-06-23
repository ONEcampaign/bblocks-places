"""Disambiguator"""

from datacommons_client import DataCommonsClient
from datacommons_client.utils.error_handling import DCStatusError
from typing import Optional

from bblocks.places.utils import clean_string, split_list
from bblocks.places.config import logger


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

    logger.info(f"Disambiguating places using Data Commons API")

    if not chunk_size:
        dcids = {}
        try:
            dcids = dc_client.resolve.fetch_dcids_by_name(
                entities, entity_type
            ).to_flat_dict()
        except DCStatusError as e:
            logger.debug(
                f"Error fetching DCIDs for entities {entities} of type {entity_type}: {e}"
            )
            logger.debug(
                "Resolving individual entities, and replacing unresolved places with None"
            )

            # if there is an error, resolve each entity individually
            for entity in entities:
                try:
                    dcids[entity] = dc_client.resolve.fetch_dcids_by_name(
                        entity, entity_type
                    ).to_flat_dict()
                except Exception as e:
                    logger.debug(
                        f"Error fetching DCID for {entity}. Resolving to None. Error: {e}"
                    )
                    dcids[entity] = None
    else:
        dcids = {}
        for chunk in split_list(entities, chunk_size):
            try:
                chunk_dcids = dc_client.resolve.fetch_dcids_by_name(
                    chunk, entity_type
                ).to_flat_dict()
                dcids.update(chunk_dcids)
            except DCStatusError as e:
                logger.debug(
                    f"Error fetching DCIDs for chunk {chunk} of type {entity_type}: {e}"
                )
                logger.debug(
                    "Resolving individual entities in the chunk, and replacing unresolved places with None"
                )

                # if there is an error, resolve each entity individually
                for entity in chunk:
                    try:
                        # chunk_dcids[entity] = dc_client.resolve.fetch_dcids_by_name(entity, entity_type).to_flat_dict()
                        chunk_dcid = dc_client.resolve.fetch_dcids_by_name(
                            entity, entity_type
                        ).to_flat_dict()
                        dcids.update(chunk_dcid)
                    except Exception as e:
                        logger.debug(
                            f"Error fetching DCID for {entity}. Resolving to None. Error: {e}"
                        )
                        chunk_dcid = {entity: None}
                        dcids.update(chunk_dcid)

    # replace empty lists with None
    for k, v in dcids.items():
        # if v is an empty list, replace it with None
        if isinstance(v, list) and len(v) == 0:
            dcids[k] = None

    return dcids


def custom_disambiguation(entity: str, disambiguation_dict: dict) -> str | None:
    """Disambiguate a given entity name using special cases.

    Args:
        entity: The entity name to disambiguate.
        disambiguation_dict: A dictionary of special cases for disambiguation.

    Returns:
        The disambiguated DCID if found in special cases, otherwise None.
    """

    cleaned_string = clean_string(entity)
    cleaned_dict = {clean_string(k): v for k, v in disambiguation_dict.items()}
    return cleaned_dict.get(cleaned_string)


def resolve_places_to_dcids(
    dc_client: DataCommonsClient,
    entities: str | list[str],
    entity_type: Optional[str],
    disambiguation_dict: Optional[dict] = None,
    chunk_size: Optional[int] = 30,
) -> dict[str, str | list | None]:
    """Disambiguate entities to their DCIDs

    This function takes ambiguous entity names and resolves them to their corresponding DCIDs using the DataCommonsClient and
    custom disambiguation rules for edge cases.

    Args:
        dc_client: An instance of DataCommonsClient.
        entities: A single entity name or a list of entity names.
        entity_type: The type of the entity (e.g., "Country"). It must be a valid Data Commons type.
        disambiguation_dict: A dictionary of special cases for disambiguation.
        chunk_size: The size of each chunk to split the list into. If None, no chunking is done.

    Returns:
        A dictionary mapping entity names to their corresponding DCIDs. If an entity name is not found, it will be mapped to None.
    """

    resolved_entities = {}
    entities_to_disambiguate = []

    # if there is any custom disambiguation, do that first
    if disambiguation_dict is not None:
        # loop through the entities checking for edge cases
        for entity in entities:
            # if the entity is an edge case, add the dcid to the dictionary and remove the entity from the list
            dcid = custom_disambiguation(entity, disambiguation_dict)
            if dcid is not None:
                resolved_entities[entity] = dcid
            else:
                # if the entity is not an edge case, add it to the list of entities to disambiguate
                entities_to_disambiguate.append(entity)
    else:
        # if there is no custom disambiguation, add all entities to the list of entities to disambiguate
        entities_to_disambiguate = entities

    # if there are still entities left, fetch the dcids from the datacommons client
    if entities_to_disambiguate:
        # fetch the dcids from the datacommons client
        dcids = fetch_dcids_by_name(
            dc_client, entities_to_disambiguate, entity_type, chunk_size
        )
        resolved_entities.update(dcids)

    return resolved_entities
