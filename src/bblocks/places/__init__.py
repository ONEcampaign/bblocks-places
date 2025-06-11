from importlib.metadata import version
from bblocks.places.resolver import PlaceResolver

from bblocks.places.main import (
    # group memberships
    get_un_members,
    get_un_observers,
    get_m49_places,
    get_sids,
    get_ldc,
    get_lldc,
    get_african_countries,
    # resolvers and filters
    resolve,
    filter_places,
    resolve_map,
    filter_african_countries,
    # Category-based filters
    get_places,
    # Other
    get_default_concordance_table,
)


__version__ = version("bblocks.places")
