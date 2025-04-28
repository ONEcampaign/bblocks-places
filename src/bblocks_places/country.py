"""Module to work with country and region level names"""

from typing import Optional, Literal
import pandas as pd
from pandas.core.dtypes.missing import isna_all

from bblocks_places.datacommons import DataCommonsResolver
from bblocks_places.config import Paths, logger
from bblocks_places.utils import clean_string



class PlaceResolver:
    """A class to resolve countries and regions to standard formats"""

    def __init__(self, *, concordance_table: Optional[pd.DataFrame] = None, dc_instance: Optional[str] = None,api_key: Optional[str] = None,url: Optional[str] = None):
        """ """

        self.__dc_client_options = {
            "dc_instance": dc_instance,
            "api_key": api_key,
            "url": url
        }

        self._dc = DataCommonsResolver(**self.__dc_client_options)
        self._concordance_table = pd.read_csv(Paths.project / "bblocks_places" / "concordance.csv") if concordance_table is None else concordance_table


    def _resolve_ambiguous_place(self, place: str) -> str:
        """Resolve an ambiguous place using the Data Commons API"""

        clean_place = clean_string(place)

        # edge cases
        if clean_place == "congo":
            return "country/COD"
        if clean_place == 'france':
            return "country/FRA"

        # get the candidates in all other cases
        try:
            candidates = self._dc.get_candidates(clean_place, place_type="Country")

        except Exception as e:
            raise e

        # if there is a single candidate return the candidate
        if isinstance(candidates[clean_place], str):
            return candidates[clean_place]

        # if there are no candidates raise error
        elif candidates[clean_place] is None:
            raise ValueError(f"place {place} not found in Data Commons")

        # if there are multiple candidates raise error
        elif len(candidates[clean_place]) > 1:
            raise ValueError(f"place {place} has multiple candidates in Data Commons: {candidates[clean_place]}")


    @staticmethod
    def _convert_place(place: str, mapper: dict) -> str:
        """Convert a single place"""

        clean_place = clean_string(place) # clean the place name

        # check if the place is in the mapping dictionary
        if clean_place not in mapper:
            raise ValueError(f"place {place} not in mapping dictionary")

        resolved_place = mapper.get(clean_place)

        if resolved_place is None:
            raise ValueError(f"place {place} does not have a resolved value")

        return resolved_place

    def _check_valid_fields(self, field: str | list[str]) -> None:
        """ """

        if isinstance(field, str):
            field = [field]

        for f in field:
            # check that the field is in the concordance table
            if f not in self._concordance_table.columns:
                raise ValueError(f"{f} not in concordance table columns")


    def get_mapper(self, places: list[str], place_type, to) -> dict[str, str]:
        """ """

        # check that the place_type and to are in the concordance table
        self._check_valid_fields([place_type, to])

        full_mapper = {clean_string(k): v for k, v in self._concordance_table.set_index(place_type)[to].to_dict().items()}

        # check if there are missing values in the mapping dictionary
        missing = [place for place in places if clean_string(place) not in full_mapper]
        if missing:
            logger.warning(f"Missing values in mapping dictionary: {missing}")

        # keep only the places that are in the concordance table
        return {place: full_mapper.get(clean_string(place)) for place in places if clean_string(place) in full_mapper}

    def convert(self, place: str, place_type, to: str):

        """ """

        # check that the place_type and to are in the concordance table
        self._check_valid_fields([place_type, to])

        # get a mapping dictionary from the concordance table
        mapper = self._concordance_table.set_index(place_type)[to].to_dict()  # create a mapping dictionary from the concordance table
        mapper = {clean_string(k): v for k, v in mapper.items()}  # clean the keys using clean_string

        # convert the place using the mapping dictionary
        resolved_place = self._convert_place(place, mapper)

        return resolved_place






