# Resolve places

`bblocks-places` makes it easy to resolve ambiguous places by building on the 
[Data Commons resolve endpoint](https://docs.datacommons.org/api/python/v2/resolve.html)
using the Google Maps API and custom disambiguation, to accurately and transparently resolve places to
stardard formats.

By default, the package will resolve places to a Data Commons [`DCID`](https://docs.datacommons.org/glossary.html#dcid)
which is a unique identifier used by Data Commons. For example the DCID for India is `country/IND`. The package is 
also able to resolve places to other standard formats including ISO3 codes, official names, groupings such as
regions and income groups, and any other [property](https://docs.datacommons.org/glossary.html#property)
in the Data Commons knowledge graph.

Let's start with a simple example. Assume we have a list of countries with non standard names, white space
and mixed capitalisation - in short, messy data.

```python
countries = ["zimbabwe", " Italy ", "USA", "Cote d'ivoire"]
```

## Basic resolving

You can easily resolve these countries to their `DCIDs`. By default if you don't specify a format to resolve to, 
places will be resolved to their Data Commons `DCIDs`

```python
from bblocks import places

resolved_countries = places.resolve_places(countries)

print(resolved_countries)
# Output:
# ['country/ZWE', 'country/ITA', 'country/USA', 'country/CIV']
```

## Resolve to different formats

You can also resolve these places to other formats such as offical names, ISO3 codes, or to a grouping such as region.

```python title="Resolve to official names"
resolved_countries = places.resolve_places(countries, to_type="name_official")

print(resolved_countries)
# Output:
# ['Zimbabwe', 'Italy', 'United States of America', 'Côte d’Ivoire']
```

```python title="Resolve to ISO3 codes"
resolved_countries = places.resolve_places(countries, to_type="iso3_code")

print(resolved_countries)
# Output:
# ['ZWE', 'ITA', 'USA', 'CIV']
```

```python title="Resolve to regions"
resolved_countries = places.resolve_places(countries, to_type="region")

print(resolved_countries)
# Output:
# ['Africa', 'Europe', 'Americas', 'Africa']
```

There are several other formats to resolve places, including:

- `dcid` - Data Commons DCID
- `name_official` - Official UN name
- `name_short` - Short name
- `iso3_code` - ISO 3 code
- `iso2_code` - ISO 2 code
- `iso_numeric_code` ISO numeric code
- `m49_code` - M49 country list code
- `dac_code` - Development Assistance Committee code
- `region` - UN region name
- `region_code` - UN region code
- `subregion` - UN subregion name
- `subregion_code` - UN subregion code
- `intermediate_region_code` - UN intermediate region code
- `intermediate_region` - UN intermediate region name
- `income_level` - World Bank income level

## Resolve to a Data Commons property

These mappings are kept in a concrdance table in the package. However, we can also resolve places to any other 
property in the knowledge graph. For example, let's resolve the countries to their administrative capitals using the
Data Commons property [`administrativeCapital`](https://datacommons.org/browser/administrativeCapital).

```python
resolved_countries = places.resolve_places(countries, to_type="administrativeCapital")

print(resolved_countries)
# Output:
# ['Harare', 'Rome', 'District of Columbia', 'Yamoussoukro']
```


The concordance table stores common mappings or mappings that might not exist in the Data Commons knowledge graph
for countries and territories. However, the package give you a lot of flexibility and customisability to resolve
different place types and use custom mappings. [Jump to the customization page](./customization.md)

## Pandas support

`bblocks-places` offers support for working with pandas Series and DataFrames easily and efficiently.

```python
import pandas as pd

df = pd.DataFrame({"country": countries})

# Let's add the ISO3 codes to the DataFrame
df["iso3_code"] = places.resolve_places(df["country"], to_type="iso3_code")
print(df)
# Output:
#       country         iso3_code
# 0     zimbabwe        ZWE
# 1     Italy           ITA
# 2     USA             USA
# 3     Cote d'ivoire   CIV
```

## Get a place mapping

You might not want to replace all the original places with their resolved values. 
You can also get a dictionary of the resolved places, which you can use to map back to the original values.

```python
resolved_countries_dict = places.map_places(countries, to_type="iso3_code")

print(resolved_countries_dict)
# Output:
# {' Italy ': 'ITA', "Cote d'ivoire": 'CIV', 'USA': 'USA', 'zimbabwe': 'ZWE'}
```

## Resolve from a known format

In the examples above we are resolving the places using Data Commons because the places are ambiguous and of
non-standard formats. When you already know the format of the places you want to resolve, you can specify it using 
the `from_type` argument and avoid relying on Data Commons to for disambiguation.

Let's say we have a list of ISO3 codes

```python
iso3_codes = ["ZWE", "ITA", "BWA", "USA"]
```

Let's resolve these ISO3 codes to their official names, by specifying their original format.

```python
resolved_countries = places.resolve_places(iso3_codes,
                                           from_type="iso3_code",
                                           to_type="name_official")

print(resolved_countries)
# Output:
# ['Zimbabwe', 'Italy', 'Botswana', 'United States of America']
```


## Handling ambiguities

The package is designed to handle ambiguities seamlessly. At a most basic level, it can handle common string issues 
such as whitespace, capitalization, and punctuation. For example, it will treat "Zimbabwe" and 
" zimbabwe " as the same place, and Cote d'Ivoire is recognized without accent marks.

```python
resolved_places = places.resolve_places([" zimbabwe ", "cote d'ivoire"],
                                        to_type="name_official")

print(resolved_places)
# Output:
# ['Zimbabwe', 'Côte d’Ivoire']
```

The package also handles more complex ambiguities such as historical and alternative names. For example
Rhodesia and Ivory Coast.

```python
resolved_places = places.resolve_places(["Rhodesia", "Ivory Coast"],
                                        to_type="name_official")

print(resolved_places)
# Output:
# ['Zimbabwe', 'Côte d’Ivoire']
```

There may be cases where a place is not found, or there may be multiple candidates for a place. 
It is important to know when these cases occur, so you can handle them appropriately. 
By default the package will raise an error when there is an ambiguity or a place is not found.

### Not found

Let's day we have a list of countries with an ambiguous name that cannot be resolved such as "Gondor"

```python
countries = ["Zimbabwe", "Italy", "Botswana", "United States", "Gondor"]
```

Trying to resolve these countries will raise an error

```python
resolved_countries = places.resolve_places(countries)

# Output:
# PlaceNotFoundError: Place not found: Gondor
```

You can choose how to handle not found values by setting the `not_found` parameter. 
You can choose to ignore them in which case their resolved
values will be set to `None` or you can specify a value for not found places such as `"place not found"`

```python title="Ignore not found places"
resolved_countries = places.resolve_places(countries, not_found="ignore")

print(resolved_countries)
# Output:
# ['country/ZWE', 'country/ITA', 'country/BWA', 'country/USA', None]
```

```python title="Set a value for not found places"
resolved_countries = places.resolve_places(countries, not_found="not found")

print(resolved_countries)
# Output:
# ['country/ZWE', 'country/ITA', 'country/BWA', 'country/USA', 'not found']
```

### Multiple candidates

There may be instances where a place could be resolved to multiple values. By default this will raise an error.
For example, trying to resolve a place to it's latitude, a short and detailed latidude exists.

```python
zim_lat = places.resolve_places("Zimbabwe", to_type="latitude")

print(zim_lat)
# Output:
# MultipleCandidatesError: Multiple candidates found for Zimbabwe: ['-19', '-19.015438']
```


You can choose how to handle these cases by setting the `multiple_candidates` to:
- `first` - First candidate
- `last` - Last candidate
- `ignore` - Return all the candidates

```python title="Use the first candidate"
zim_lat = places.resolve_places("Zimbabwe",
                                to_type="latitude",
                                multiple_candidates="first")

print(zim_lat)
# Output:
# '-19'
```

```python title="Use the last candidate"
zim_lat = places.resolve_places("Zimbabwe",
                                to_type="latitude",
                                multiple_candidates="last")

print(zim_lat)
# Output:
# '-19.015438'
```

```python title="Use all the candidates"
zim_lat = places.resolve_places("Zimbabwe",
                                to_type="latitude",
                                multiple_candidates="ignore")

print(zim_lat)
# Output:
# ['-19', '-19.015438']
```

## Custom mapping

For cases where a place cannot be resolved or you want to map a place to a different value, you can set the
`custom_mapping` parameter. For example let's map "Gondor" to a fictitious DCID such as `country/GON`.

```python
countries = ["Zimbabwe", "Italy", "Botswana", "United States", "Gondor"]
resolved_countries = places.resolve_places(countries,
                                           custom_mapping={"Gondor": "country/GON"})

print(resolved_countries)
# Output:
# ['country/ZWE', 'country/ITA', 'country/BWA', 'country/USA', 'country/GON']
```