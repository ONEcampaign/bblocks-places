# Customization and extensibility

The `bblocks-places` package is designed to be  extensible and customisable. You will have seen in the
previous pages that the default functionality is geared towards the most common use case - country-level data.
But you can customize the functionality to work with any type of place and have full control over how place resolving
behaves by using your own concordance table or override the default mappings with your own.

## The `PlaceResolver` object

To have full control over place resolver behaviour, custom place mappings and to adjust Data Commons settings
use the `PlaceResolver` object. This object allows you to set a a concordance table, custom mappings, the place type
to resolve for (e.g. Countries), and specify Data Commons settings.

All the functionality described in previous pages such as [`resolve`](resolve-places.md) functionality and
[filter](filter-places.md) functionality is built on on a `PlaceResolver` object using a default concordance table,
default place mappings, only resolving places categorised as countries, and using the ONE Campaign Data Commons 
instance. 

For instance, let's resolve our previous list of countries using the `PlaceResolver` object with the default
settings. 

```python
countries = ["zimbabwe", " Italy ", "USA", "Cote d'ivoire"]
```

First let's instantiate the object

```python
custom_resolver = places.PlaceResolver(concordance_table="default", 
                                       custom_disambiguation="default",
                                       dc_entity_type="Country"
                                       )
```

The `custom_resolver` will use the concordance table that comes with the package, any custom
disambiguation rules defined in the package, and only resolve for the Data Commons entity type `Country`.
It will also rely on the ONE Campaign Data Commons instance to resolve places.

```python
resolved_places = custom_resolver.resolve_places(countries, to_type="iso3_code")

print(resolved_places)
# Output:
# ['ZWE', 'ITA', 'USA', 'CIV']
```

Using the `resolve` method above yields the same results as we saw 
[earlier](../getting-started/#resolve-ambiguous-places) using the `resolve` function.

Additional useful methods in the `PlaceResolver` object include:

- `filter` to filter places based on one or more categories
- `resolve_map` to get a dictionary of places with their resolved values




The `PlaceResolver` object is customisable. You can use the default settings and add new custom disambiguation 
rules or use completely different rules. you can use your own custom concordance table or not use one at all.
You can specify a different entity type to resolve for, or not specify one at all. And you can use a different Data
Commons instance. 

The next sections will guide you through this customisation. 


## Add new disambiguation rules

You will recall that you can override any place resoltion by setting the
[`custom_mapping`](../resolve-places/#custom-mapping) parameter in the `resolve` function.


For example let's say we want to resolve "Gondor" to its (fictitious) DCID which isn't mapped by default.
Calling `resolve` will raise an error. But we can set the `custom_mapping` parameter:

```python hl_lines="3"
gondor_dcid = custom_resolver.resolve_places("Gondor",
                                             custom_mapping={"Gondor": "country/GON"})

print(gondor_dcid)
# Output:
# 'country/GON'
```

Using this custom disambiguation rule we bypass the resolving logic used by Data Commons.

Instead of having to set the `custom_mapping` parameter, we can add this mapping to the object so that "Gondor"
is recognised automatically.

```python
custom_resolver.add_custom_disambiguation({"Gondor": "country/GON"})

gondor_dcid = resolved_countries = custom_resolver.resolve_places("Gondor")

print(gondor_dcid)
# Output:
# 'country/GON'
```

The `add_custom_disambiguation` is used to add a mapping of a place name to its `DCID`. The package logic will handle 
common issues such as white space and mixed capitalisation. For example:

```python
gondor_dcid = custom_resolver.resolve_places(" gondor")

print(gondor_dcid)
# Output:
# 'country/GON'
```

## Override disambiguation rules

The default disambiguation rules used by the object and Data Commons can be overridden. There are cases where
disambiguation is inherently difficult - should `Congo` resolve to the Republic of Congo or the Democratic
Republic of Congo (DRC)? The default behaviour of the package in this case is to resolve to "Congo"
(`DCID = 'country/COG'`). You may want to change this behaviour so that "Congo" resolves to DRC by default.

```python

custom_resolver.add_custom_disambiguation({"Congo": "country/COD"})

congo_name = resolved_countries = custom_resolver.resolve_places("Congo", to_type="name_official")

print(congo_name)
# Output:
# 'Democratic Republic of the Congo'
```

## Set custom disambiguation rules

Instead of adding new rules to the object, you can set these rules at instantiation.

For example, let's make a place resolver object to resolve fantasy places.

```python hl_lines="9"
custom_rules = {"Gondor": "country/GON",
                "Wakanda": "country/WAK",
                "Tatooine": "country/TAT",
                "Narnia": "country/NAR",
                "Cybertron": "country/CYB"
                }

custom_resolver = places.PlaceResolver(concordance_table="default",
                                       custom_disambiguation=custom_rules,
                                       dc_entity_type="Country"
                                       )
```

Now let's get the DCID for "Gondor"

```python
gondor_dcid = custom_resolver.resolve_places(" gondor")

print(gondor_dcid)
# Output:
# 'country/GON'
```

You can also choose not to use any disambiguation rules

```python hl_lines="2"
custom_resolver = places.PlaceResolver(concordance_table="default",
                                       custom_disambiguation=None, # (1)!
                                       dc_entity_type="Country")
```

1. You can also not specify `custom_disambiguation` parameter which is set to `None` by default.

!!! warning
    It is not recommended to completely override or not use the default disambiguation rules. At the time
    this documentation is written, several places are not correctly resolved by the Data Commons resolve
    endpoint and can cause unexpected issues such as false matched or missed matches. For example the country
    "Cabo Verde" (in its official form rather than "Cape Verde") does not correctly resolve to the DCID 
    `country/CPV`. 

    Several other edge cases are taken care of by the package. You can see the default custom disambiguation rules
    by running `places.PlaceResolver._EDGE_CASES`

    If you find any missed edge cases or other resolving bugs please 
    [open an issue](https://github.com/ONEcampaign/bblocks-places/issues).


## Use a custom concordance table

In the previous section we managed to add custom disambiguation logic for our fantasy places. But we are only
able to resolve these places to their `DCIDs`. We can use a custom concordance table to map these places to 
different formats suchs as ISO 3 codes or regions. The only requirement is that the concordance table needs one column
with the `DCIDs` of the places which is used as an index and at least one other column with any mapping. The `DCIDs`
column should be named `dcid`.

Let's create a concordance table for our fantasy places.

```python
import pandas as pd

concordance_df = pd.DataFrame({
    "name": ["Gondor", "Wakanda", "Tatooine", "Narnia", "Cybertron"],
    "dcid": ["country/GON", "country/WAK", "country/TAT", "country/NAR", "country/CYB"],
    "region": ["Middle-earth", "Africa", "Outer Rim", "Fantasyland", "Space"],
})

print(concordance_df)
# Output:
#       name        dcid            region
# 0     Gondor      country/GON     Middle-earth
# 1     Wakanda     country/WAK     Africa
# 2     Tatooine    country/TAT     Outer Rim
# 3     Narnia      country/NAR     Fantasyland
# 4     Cybertron   country/CYB     Space
```

Now let's instantiate a custom `PlaceResolver` object with our concordance table and resolve a place to its region.

```python hl_lines="1"
custom_resolver = places.PlaceResolver(concordance_table=concordance_df)

gondor_region = custom_resolver.resolve_places("Gondor", from_type="name", to_type="region")

print(gondor_region)
# Output:
# 'Middle-earth'
```

!!! Note
    The example above uses fictitious fantasy places which do not exist in the Data Commons
    knowledge graph, so disambiguation won't work. You can set custom disambiguation rules at instantiation
    as shown before or use the `custom_mapping` parameter when calling the `resolve` method. If the places
    exist in the knowledge graph disambiguation will work as expected.


You can also choose to not use a concordance table at all, in which case Data Commons will be used for all 
place resolution

```python
custom_resolver = places.PlaceResolver(concordance_table=None)  # (1)! 

zim_iso3 = custom_resolver.resolve_places("Zimbabwe ", to_type="countryAlpha3Code")

print(zim_iso3)
# Output:
# 'ZWE'
```

1. You can also instantiate the object without specifying `concordance_table` which by default will be set to `None`

## Specify the place type

The Data Commons resolve endpoint allows you to specify the entity types you want to resolve for. 
This is useful if you know the entity type your custom resolver is going to resolve for. 

For example if you are only going to resolve countries, you can specify the entity type as `Country`. 
This is the dafault entity type used by the package. This will prevent several ambiguous cases. 
For example the name "Italy" can refer to the country in Europe or the city in Texas.

By not specifying the entity type, all types are considered where there may be multiple candidates for a place.

```python
custom_resolver = places.PlaceResolver(dc_entity_type=None)  # (1)!

print(custom_resolver.resolve_places("Italy", to_type="name"))
# Output:
# MultipleCandidatesError: Multiple candidates found for Italy : ['Italy', ['Italy', 'Italy, Texas']]

```

1. You can also instantiate the object without specifying `dc_entity_type` which by default will be set to `None`

The entity type can be set to any [Data Commons place type](https://docs.datacommons.org/place_types.html).

```python title="Country place type"
custom_resolver = places.PlaceResolver(dc_entity_type="Country")

print(custom_resolver.resolve_places("Italy", to_type="name"))
# Output:
# 'Italy'
```

```python title="City place type"
custom_resolver = places.PlaceResolver(dc_entity_type="City")

print(custom_resolver.resolve_places("Italy Texas", to_type="name"))
# Output:
# 'Italy'
```

## Data Commons settings

By default the package uses ONE Campaign's instance of Data Commons which currently
doesn't have an API key or rate limits. You can create a `PlaceResolver` object that
uses any other instance of Data Commons or the base instance of [Data Commons](https://datacommons.org/) to
resolve places.

To do this set the Data Commons API settings in the `dc_api_settings` parameter at instantiation
You can set the:

- `api_key` - the API key for the custom instance
- `dc_instance` - publicly resolvable DNS hostname
- `url` - private/non-resolvable Data Commons address

```python
custom_resolver = places.PlaceResolver(dc_api_settings = {dc_instance: "datacommons.mycompany.org", 
                                                          api_key: "YOUR_API_KEY"
                                                          }
                                       )

```

Read more about using a Data Commons API client [here](https://docs.datacommons.org/api/python/v2/#create-a-client)
