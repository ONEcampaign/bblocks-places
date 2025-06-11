# bblocks-places
A package for resolving, standardizing, and work with countries, regions, and other geographical or political entities.

Working with country data is deceptively tricky. There are many different ways to represent the same place or country. 
The same place might be labeled as “South Korea”, “Republic of Korea”, “KOR”, or “KR”, depending on the source. These
inconsistencies lead to a lot of time spent cleaning and standardizing data, and can lead to errors in analysis 
if not handled properly. `bblocks-places` solves this problem by providing a simple, consistent interface to resolve, 
standardize, and map geographic or political entities across datasets.
It allows you to easily:
- Disambiguate and resolve free-text place names to standard identifiers
- Convert between formats (e.g., ISO codes, official names, etc)
- Filter and group places based on shared attributes (e.g., region, income level, UN membership)
- Customize resolution using your own concordance or override mappings


🔗 __Powered by Data Commons__.
This package is built on top of Data Commons, an open knowledge graph that aggregates data from trusted sources like 
the UN, World Bank, and national statistical offices. `bblocks-places` uses the Data Commons resolve endpoint to 
disambiguate and resolve free-text place names, and if a specific place format is not available in a concordance table, 
it attempts to find the format as a property in the Data Commons graph.

### Why `bblocks-places`?

There are several excellent Python libraries for working with country names and codes, such as:

- country_converter — for ISO/M49 name/code conversions
- pycountry — for standardized country, subdivision, and language metadata
- iso3166 — for direct access to ISO 3166 country codes

These are mature, well-maintained tools that may be ideal for static, ISO-based mappings or lightweight lookups.

While those tools work well, `bblocks-places` is designed for more flexible, accurate, and extensible workflows. 
It offers:
- __Customizable concordance__: Use your own mappings or augment the default concordance with project-specific codes, 
aliases, or structures.
- __Strict and transparent disambiguation__:
When using name-based disambiguation, the package explicitly flags ambiguous or unresolved cases. You can choose how 
to handle: No match → raise an error, return None, or return a specific value, multiple matches → raise, return all, 
or take first. This helps avoid silent mismatches and reduces false positives or negatives.
- __Broad support for many types of places__:
By integrating with Data Commons, the package can resolve countries, subnational regions, counties, cities, and more 
— any entity in the knowledge graph. This makes it useful not just for national-level data, but for granular 
geographic analysis as well.

## Usage

Install the package using pip:
>TODO: release to PyPI. Install from GitHub for now:
```bash
pip install git+https://github.com/ONEcampaign/bblocks-places.git
```

## Basic usage

Import the package:
```python
from bblocks import places
```

### Resolving places

In most cases, analysts are working with country-level data. Convenient functionality is built for this case,
but the package offers more flexibility (jump to the customization section)

Resolve a list of ambiguous countries
```python
countries = ["Zimbabwe", "Italy", "Botswana", "United States"]
resolved_countries = places.resolve(countries)
print(resolved_countries)
# Output:
# ['country/ZWE', 'country/ITA', 'country/BWA', 'country/USA']
```

By default this will resolve countries to their Data Commons IDs (DCIDs). You can specify a different format
for example ISO3
```python
resolved_countries = places.resolve(countries, to_type="iso3_code")
print(resolved_countries)
# Output:
# ['ZWE', 'ITA', 'BWA', 'USA']
```

Places can also be resolved to standard groupings like region or income level
```python
resolved_countries = places.resolve(countries, to_type="region")
print(resolved_countries)
# Output:
# ['Africa', 'Europe', 'Africa', 'Americas']
```

These mappings are all based on a default concordance table that comes with the package. To see the
concordance table call `places.get_default_concordance_table()`

You can also resolve places to a format that is not in the default concordance table. For example to get countries'
capitals, which are known in the Data Commons graph as property `administrativeCapital`, you can run:
```python
resolved_countries = places.resolve(countries, to_type="administrativeCapital")
print(resolved_countries)
# Output:
# ['Harare', 'Rome', 'Gaborone', 'District of Columbia']
```

Resolving places in a pandas DataFrame is also easy and efficient.
```python 
import pandas as pd
df = pd.DataFrame({"country": ["Zimbabwe", "Italy", "Botswana", "United States"]})

# Let's add the ISO3 codes to the DataFrame
df["iso3_code"] = places.resolve(df["country"], to_type="iso3_code")
print(df)
# Output:
#      country          iso3_code
# 0    Zimbabwe         ZWE
# 1    Italy            ITA
# 2    Botswana         BWA
# 3    United States    USA
```

You might not want to replace all the original places with their resolved versions. You can also get
a dictionary of the resolved places, which you can use to map back to the original values.
```python
resolved_countries_dict = places.resolve_map(countries, to_type="iso3_code")
print(resolved_countries_dict)
# Output:
# {'Zimbabwe': 'ZWE', 'Italy': 'ITA', 'Botswana': 'BWA', 'United States': 'USA'}
```

In the examples above we are disambiguating the places using Data Commons. At times you already know the format of the 
places, and you want to map them to a different format. It is more efficient to specify their format than to 
disambiguate them.

```python
# Let's say we have a list of ISO3 codes and we want to convert them to ISO2 codes
iso3_codes = ["ZWE", "ITA", "BWA", "USA"]
resolved_countries = places.resolve(iso3_codes, from_type="iso3_code", to_type="iso2_code")
print(resolved_countries)
# Output:
# ['ZW', 'IT', 'BW', 'US']
```

__Handling ambiguities__

The package is designed to handle ambiguities seamlessly. At a most basic level, it can handle common string issues such
as whitespace, capitalization, and punctuation. For example, it will treat "Zimbabwe" and " zimbabwe " as the same place,
and Cote d'Ivoire is recognized without accent marks.

```python
resolved_places = places.resolve([" zimbabwe ", "cote d'ivoire"], to_type="iso3_code")
print(resolved_places)
# Output:
# ['ZWE', 'CIV']
```

The package also handles more complex ambiguities such as historical and alternative names. For example:

```python
resolved_places = places.resolve(["Rhodesia", "Ivory Coast"], to_type="name_official")
print(resolved_places)
# Output:
# ['Zimbabwe', 'Côte d’Ivoire']
```

When resolving places, there may be cases where a place is not found, or there may be multiple candidates for a place. It is
important to know when these cases occur, so you can handle them appropriately. By default the package will
raise an error when there is an ambiguity or a place is not found.

```python
# Let's say we have a list of countries with some ambiguous names like "Gondor" from the Lord of the Rings
countries = ["Zimbabwe", "Italy", "Botswana", "United States", "Gondor"]
resolved_countries = places.resolve(countries)
# Output:
# PlaceNotFoundError: Place not found: Gondor
```

You can also choose to set not found values to ``None`` or a specific value.
```python
resolved_countries = places.resolve(countries, not_found="ignore")
print(resolved_countries)
# Output:
# ['country/ZWE', 'country/ITA', 'country/BWA', 'country/USA', None]
```
```python
resolved_countries = places.resolve(countries, not_found="not found")
print(resolved_countries)
# Output:
# ['country/ZWE', 'country/ITA', 'country/BWA', 'country/USA', 'not found']
```

If you know the value for these ambiguouse places, you can also set the value to that.
```python
resolved_countries = places.resolve(countries, not_found="not found", custom_mapping={"Gondor": "country/GON"})
print(resolved_countries)
# Output:
# ['country/ZWE', 'country/ITA', 'country/BWA', 'country/USA', 'country/GON']
```

There are situations where a place is ambiguous and has multiple candidates. For example resolving to
latitudes, a detailed or a shorter latidude exists.
```python
resolved_countries = places.resolve("Zimbabwe", to_type="latitude")
print(resolved_countries)
# Output:
# MultipleCandidatesError: Multiple candidates found for Zimbabwe: ['-19', '-19.015438']
```

You can choose how to handle these cases by setting the ``multiple_candidates`` parameter. By default
it will raise an error, but you can also choose to return all candidates, use the first candidate,
or use the last candidate.
```python
# return all the candidates
resolved_countries = places.resolve("Zimbabwe", to_type="latitude", multiple_candidates="ignore")
print(resolved_countries)
# Output:
# ['-19', '-19.015438']
```
```python
# return the first candidate
resolved_countries = places.resolve("Zimbabwe", to_type="latitude", multiple_candidates="first")
print(resolved_countries)
# Output:
# '-19'
```
```python
# return the last candidate
resolved_countries = places.resolve("Zimbabwe", to_type="latitude", multiple_candidates="last")
print(resolved_countries)
# Output:
# '-19.015438'
```

### Filtering places
You can filter places based on some categories like regions or income levels.

```python
countries = ["Zimbabwe", "Italy", "Botswana", "United States"]

# Let's say we have a list of countries and we want to filter them for high income countries
filtered_countries = places.filter_places(countries, {"income_level": "High income"})
print(filtered_countries)
# Output:
# ['Italy', 'United States']

# Set ``raise_if_empty=True`` to be notified when no places match
places.filter_places(countries, {"region": "Oceania"}, raise_if_empty=True)

# You can also filter using multiple categories at once
lmic_africa = places.filter_places(
    countries,
    filters={"region": "Africa", "income_level": "Lower middle income"},
)
print(lmic_africa)
# Output:
# ['Zimbabwe']

# ``raise_if_empty`` can also be used here
places.filter_places(
    countries,
    filters={"region": "Oceania", "income_level": "Low income"},
    raise_if_empty=True,
)
```

Helper functions for specific filtering exists, for example to filter for African countries
```python
african_countries = places.filter_african_countries(countries)
print(african_countries)
# Output:
# ['Zimbabwe', 'Botswana']
```


### Getting places that belong to a specific category

Aside from resolving and filtering places, you might want to get all the places that belong to a specific category,
for example all official UN member states or all African countries. This package has several useful
functions to do this.

Let's get all the countries that are in Europe
```python
european_countries = places.get_places(
    filters={"region": "Europe"},
    place_format="name_official",
    raise_if_empty=True,
)
print(european_countries)
# Output:
# ['Åland Islands', 'Albania', 'Andorra', 'Austria', 'Belarus', 'Belgium'...]
```

You could also get places for multiple categores and values at once. For example Lower middle income countries in Africa
```python
lmic_africa = places.get_places(
    filters={"region": ["Africa"], "income_level": ["Lower middle income"]},
    place_format="name_official",
    raise_if_empty=True,
)
print(lmic_africa)
# Output:
# ['Zimbabwe']
```

Several helper functions exist for specific categories, for example to get all UN member states
```python
un_member_states = places.get_un_members(place_format="name_official")
print(un_member_states)
# Output:
# ['Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda'...]
```
Other helper functions include:
- `get_un_observers` - get all UN observer states
- `get_m49_places` - get all M49 places
- `get_sids` - get all Small Island Developing States
- `get_ldc` - get all Least Developed Countries
- `get_lldc` - get all Landlocked Developing Countries
- `get_african_countries` - get all African countries

## Customization and extensibility

The package is designed to be extensible and customizable. You can use your own concordance table, 
or override the default mappings with your own. The main object of the package is the `PlaceResolver` 
class, which gives you full control over how place resolution behaves.

### Use your own concordance table or don't use one at all
By default the object used a built-in concordance table, which is tailored to the common use case - working
with country-level data. It contains concordance mappings for countries and areas generally recognised by
the United Nations M49 list which is used for statistical purposes and contains common groupings like
UN defined regions and World Bank income levels.

You can specify you own concordance table by passing a pandas DataFrame to the `concordance_table` parameter
at instantiation. The concordance table should have at least one column with the DataCommons ID and one column
with any other mapping. The DataCommons ID column should be named `dcid`.

```python
import pandas as pd
concordance_df = pd.DataFrame({
    "name": ["Gondor", "Wakanda", "Tatooine", "Narnia", "Cybertron"],
    "dcid": ["country/GON", "country/WAK", "country/TAT", "country/NAR", "country/CYB"],
    "region": ["Middle-earth", "Africa", "Outer Rim", "Fantasyland", "Space"],
})

custom_resolver = places.PlaceResolver(concordance_table=concordance_df)

```

This will allow you to run some custom resolutions like
```python
gondor_region = custom_resolver.resolve("Gondor", from_type="name", to_type="region")
print(gondor_region)
# Output:
# 'Middle-earth'
```

__NOTE__: The example above is fictitious and the places do not exist in the Data Commons graph, so
disambiguation won't work. You can use the `custom_mapping` parameter to add mappings for these places
(or any places that are not in the Data Commons graph) to the object.
```python
custom_mapping = {
    "Gondor": "country/GON",
    "Wakanda": "country/WAK",
    "Tatooine": "country/TAT",
    "Narnia": "country/NAR",
    "Cybertron": "country/CYB"
}

custom_resolver = places.PlaceResolver(concordance_table=concordance_df, custom_disambiguation=custom_mapping)
```

This will allow you to resolve these places, bypassing the Data Commons resolver
```python
name = custom_resolver.resolve("gondor ", to_type="name")
print(name)
# Output:
# 'Gondor'
```

You can also instantiate an object without a concordance table, which will use the Data Commons
for all resolutions.

```python
custom_resolver = places.PlaceResolver(concordance_table=None)

```

This will allow use the Data Commons graph for all resolutions
```python
iso3 = custom_resolver.resolve("Zimbabwe ", to_type="countryAlpha3Code")
print(iso3)
# Output:
# 'ZWE'
```

The Data Commons resolve endpoint allows you to specify the entity types you want to resolve for. This
is useful if you know the entity type your custom resolver is going to resolve for. For example if you
are only going to resolve countries, you can specify the entity type as `Country`. This will prevent
several ambiguous cases. For example the name "Italy" can refer to the country or the city in Texas.

```python
# not specifying the entity type might cause ambiguous cases
custom_resolver = places.PlaceResolver(concordance_table = None, custom_disambiguation = None)
print(custom_resolver.resolve("Italy", to_type="name"))
# Output:
# MultipleCandidatesError: Multiple candidates found for Italy : ['Italy', ['Italy', 'Italy, Texas']]
```

Specifying the entity type will prevent this
```python
custom_resolver = places.PlaceResolver(concordance_table=None, custom_disambiguation=None, dc_entity_type="Country")
print(custom_resolver.resolve("Italy", to_type="name"))
# Output:
# 'Italy'
```


