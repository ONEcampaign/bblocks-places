from importlib.metadata import version
from bblocks.places.resolver import PlaceResolver

from bblocks.places.main import (
    get_un_members,
    get_un_observers,
    get_m49_places,
    get_sids,
    get_ldc,
    get_lldc,
    get_african_countries,

    resolve_places,
    filter_places,
    resolve_places_mapping,

    filter_african_countries,
    get_places_by
                                 )


__version__ = version("bblocks.places")
