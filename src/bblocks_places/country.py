"""Module to work with country and region level names"""

from typing import Optional, Literal

import numpy as np
import pandas as pd
from datacommons_client import DataCommonsClient

from bblocks_places.config import (
    Paths,
    logger,
    MultipleCandidatesBehavior,
)
from bblocks_places.datacommons import DataCommonsResolver
from bblocks_places.utils import clean_string


class ConcordanceTable:
    """A class to hande the concordance using the concordance table"""

    def __init__(self):

        self._concordance_table = pd.read_csv(
            Paths.project / "bblocks_places" / "concordance.csv"
        )

        self._ALLOWED_SOURCES = ("dcid", "name", "iso2_code", "iso3_code", "name_short")
        self._ALLOWED_TARGETS = (
            "dcid",
            "name",
            "iso2_code",
            "iso3_code",
            "name_short",
            "income_level",
        )

    def check_allowed(self, source: str, target: str):
        """Check that the source and target are in the allowed sources and targets"""

        if source not in self._ALLOWED_SOURCES:
            raise ValueError(
                f"Invalid source: {source}. Allowed sources are {self._ALLOWED_SOURCES}"
            )
        if target not in self._ALLOWED_TARGETS:
            raise ValueError(
                f"Invalid target: {target}. Allowed targets are {self._ALLOWED_TARGETS}"
            )

    def get_full_mapper(self, source, target):
        """Get a full mapper of the concordance table for a source to target"""

        if source == target:
            return (
                self._concordance_table.assign(source_dup=lambda d: d[source])
                .dropna(subset=source)
                .set_index("source_dup")[target]
                .to_dict()
            )

        return (
            self._concordance_table.dropna(subset=source)
            .set_index(source)[target]
            .to_dict()
        )

    def get_mapper(self, places, source, target):
        """Get a mapper for places where if a place is not found, it is set to None"""

        self.check_allowed(source, target)

        mapper = self.get_full_mapper(source, target)
        clean_mapper = {clean_string(k): v for k, v in mapper.items()}

        for place in places:
            clean_place = clean_string(place)
            if clean_place not in clean_mapper:
                mapper[place] = None

        return mapper

    @staticmethod
    def handle_not_found(mapper: dict, not_found: str = "raise") -> dict[str, str]:
        """Handle the not found logic for a list of places"""

        for place, resolved in mapper.items():
            if resolved is None or resolved is np.nan:
                if not_found == "raise":
                    raise ValueError(f"Place not found: {place}")
                elif not_found == "ignore":
                    logger.warn(f"Place not found: {place}")
                else:
                    logger.warn(f"Place not found: {place}. Replacing with {not_found}")
                    mapper[place] = not_found

        return mapper

    def map(
        self, places: list[str], source, target, not_found: str = "raise"
    ) -> dict[str, str]:
        """Get a mapping of places from the concordance table"""

        self.check_allowed(source, target)
        mapper = self.get_mapper(places, source, target)
        mapper = self.handle_not_found(mapper, not_found)

        return mapper


class PlaceResolver:
    """A class to resolve countries and regions to standard formats"""

    def __init__(self):

        self._disambiguator = DataCommonsResolver(
            DataCommonsClient(dc_instance="datacommons.one.org")
        )
        self._concordance = ConcordanceTable()

    def get_mapper(
        self,
        places: str | list[str],
        to: str,
        place_type: Optional[str] = None,
        not_found="raise",
        multiple: MultipleCandidatesBehavior | str = "raise",
        custom_mapping: Optional[dict] = None,
    ) -> dict[str, str | None]:
        """Get a dictionary mapping of places to the target format"""

        if isinstance(places, str):
            places = [places]

        if isinstance(places, pd.Series):
            places = list(places.unique())

        # if a custom mapping is provided, remove the keys from the list of places to convert
        if custom_mapping:
            places = [p for p in places if p not in custom_mapping.keys()]

            # if all the places are in the custom mapping, return the custom mapping
            if len(places) == 0:
                return custom_mapping

        # if the place_type is not provided, resolve the places to their Data Commons IDs first then map them to the target format
        if not place_type:
            # disambiguate the places using Data Commons
            places = self._disambiguator.resolve_ambiguous(
                places, not_found=not_found, multiple=multiple
            )

            if to != "dcid":
                # get the mapping of the places to their Data Commons IDs
                dcids_mapper = self._concordance.get_mapper(
                    places.values(), source="dcid", target=to
                )
                # map the values in placed to the keys in dcids_mapper
                places = {
                    place: dcids_mapper.get(dcid) for place, dcid in places.items()
                }

            # handle the not found logic
            places = self._concordance.handle_not_found(places, not_found)

            # add the custom mapping to the mapper
            places = places | custom_mapping if custom_mapping else places

            return places

        # if place_type is provided, get the mapping of the places to the target format
        else:
            mapper = self._concordance.map(
                places, source=place_type, target=to, not_found=not_found
            )
            mapper = mapper | custom_mapping if custom_mapping else mapper

            return mapper

    def convert(
        self,
        places: str | list[str] | pd.Series,
        place_type: Optional[str] = None,
        to: Optional[str] = "dcid",
        not_found: Literal["raise", "ignore"] = "raise",
        multiple: Literal["raise", "first", "ignore"] = "raise",
        custom_mapping: Optional[dict] = None,
    ):
        """Convert places to a target format"""

        mapper = self.get_mapper(
            places, place_type, to, not_found, multiple, custom_mapping
        )

        # convert the places to the target format
        if isinstance(places, str):
            return mapper[places]

        elif isinstance(places, list):
            return [mapper[p] for p in places]

        elif isinstance(places, pd.Series):
            return places.map(mapper)

        else:
            raise ValueError("places must be a string or a list of strings")
