"""Data Commons places and entities resolver

This module provides a convenient wrapper to interact with places in Data Commons using the Data Commons API,
with functionality to resolve DCIDs or ambiguous names to Data Commons properties, and get candidates
that match ambiguous places using the Data Commons API.

To use first instantiate the DataCommonsResolver class with the desired parameters to access a Data Commons instance.
By default, the ONE Campaign Data Commons instance is used - datacommons.one.org.

>>> resolver = DataCommonsResolver()

Get the candidates for a place or places

>>> resolver.get_candidates("Zimbabwe") # returns the DCID for Zimbabwe: {"Zimbabwe": ["country/ZWE"]}

Convert the candidates to a specific property
>>> resolver.convert("Zimbabwe", to="countryAlpha3Code") # return the ISO3 code for Zimbabwe: "ZWE"

"""

from bblocks_places.datacommons.datacommons_wrapper import DataCommonsResolver