"""Module to work with country and region level names"""

from typing import Optional
import pandas as pd

from bblocks_places.datacommons import DataCommonsResolver
from bblocks_places.config import Paths, logger
from bblocks_places.utils import clean_string


class PlaceResolver:
    """A class to resolve countries and regions to standard formats"""

    def __init__(self):
        """ """

        self._dc = DataCommonsResolver()
        self._concordance_table = pd.read_csv(Paths.project / "bblocks_places" / "concordance.csv")

    def _concordance_mapper(self, place_type, to) -> dict[str, str]:
        """Get a dictionary from the concordance table mapping place_type to the target format"""

        # check that the place_type and to are in the concordance table
        if place_type not in self._concordance_table.columns:
            raise ValueError(f"place_type {place_type} not in concordance table")
        if to not in self._concordance_table.columns:
            raise ValueError(f"to {to} not in concordance table")

        # if to and place_type are the same, raise a warning
        if to == place_type:
            logger.warn("`place_type` and `to` are the same. Standardizing and returning places in the same format")
            return self._concordance_table.assign(to_copy = lambda d: d[place_type]).set_index("to_copy")[to].to_dict()

        return self._concordance_table.set_index(place_type)[to].to_dict()

    @staticmethod
    def _filter_mapper(places, mapper, not_found) -> dict[str, str]:
        """Gets a mapper only for specified places
        It handles the not_found behavior
        """

        clean_mapper = {clean_string(k): v for k, v in mapper.items()}

        # remove any duplicates from the list of places
        places = list(set(places))

        d = {} # initialize a dictionary to store the mapping

        # loop through each place and check if it is in the mapping
        for place in places:
            clean_place = clean_string(place)
            if clean_place not in clean_mapper:
                if not_found == "raise":
                    raise ValueError(f"place {place} not in concordance table")
                elif not_found == "ignore":
                    logger.warn(f"place {place} not in concordance table")
                    d[place] = None
                else:
                    logger.warn(f"place {place} not in concordance table. replacing with {not_found}")
                    d[place] = not_found
            else:
                d[place] = clean_mapper[clean_place]

        if len(d) == 0:
            raise ValueError("No places found in the mapping")

        return d


    def resolve_to_dcid(self, places, not_found="raise") -> dict:
        """ """

        place_candidates = self._dc.get_candidates(places, place_type="Country")

        for place, candidates in place_candidates.items():
            if candidates is None:
                if not_found == "raise":
                    raise ValueError(f"Place not found: {place}")
                elif not_found == "ignore":
                    logger.warn(f"Place not found: {place}")
                    place_candidates[place] = None
                else:
                    logger.warn(f"Place not found: {place}. replacing with {not_found}")
                    place_candidates[place] = not_found

            if isinstance(candidates, list) and len(candidates) > 1:
                if not_found == "raise":
                    raise ValueError(f"Multiple candidates found for {place}: {candidates}")
                elif not_found == "ignore":
                    logger.warn(f"Multiple candidates found for {place}: {candidates}. Returning None.")
                    place_candidates[place] = None
                else:
                    logger.warn(f"Multiple candidates found for {place}: {candidates}. Replacing with {not_found}.")
                    place_candidates[place] = not_found

        return place_candidates

    def get_mapper(self, places: str | list[str], to: str, place_type: Optional[str] = None, not_found="raise", custom_mapping: Optional[dict] = None) -> dict[str, str]:
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



        if not place_type:
            places = self.resolve_to_dcid(places, not_found=not_found)
            mapper = self._concordance_mapper("dcid", to)

            for place, dcid in places.items():
                if dcid is not None:
                    if dcid not in mapper:
                        if not_found == "raise":
                            raise ValueError(f"Place {place} not found in concordance table")
                        elif not_found == "ignore":
                            logger.warn(f"Place {place} not found in concordance table. Returning None.")
                            places[place] = None
                        else:
                            logger.warn(f"Place {place} not found in concordance table. Replacing with {not_found}.")
                            places[place] = not_found

                    places[place] = mapper[dcid]


            # add the custom mapping to the mapper
            places = places | custom_mapping if custom_mapping else places
            return places

        else:


            # get the mapping of the places to the target format
            mapper = self._concordance_mapper(place_type, to)
            mapper = self._filter_mapper(places, mapper, not_found)

            # add the custom mapping to the mapper
            mapper = mapper | custom_mapping if custom_mapping else mapper

            return mapper

    def convert(self,
                places: str | list[str] | pd.Series,
                place_type: Optional[str] = None,
                to: Optional[str] = "dcid",
                not_found="raise",
                custom_mapping: Optional[dict] = None):
        """ """

        mapper = self.get_mapper(places, place_type, to, not_found, custom_mapping)

        # convert the places to the target format
        if isinstance(places, str):
            return mapper[places]

        elif isinstance(places, list):
            return [mapper[p] for p in places]

        elif isinstance(places, pd.Series):
            return places.map(mapper)

        else:
            raise ValueError("places must be a string or a list of strings")



