# Getting started with `bblocks-places`

This page walks you through the basic steps to install `bblocks-places` and start resolving and standardizing places

## Installation

You can install the package as part of the broader `bblocks` distribution or as a standalong package

```python title="Option 1: install via bblocks with extras"
pip install bblocks[places]
```

```python title="Option 2: standalone installation"
pip install bblocks-places
```

Now you can import the package.

```python
from bblocks import places
```

## Resolve places

Once installed and imported `bblocks-places` you can use the convenient functionality to start working with country-level data.

Lets start with a very simple example. Say we have a list of countries with non standard names

```python
countries = ["zimbabwe", " Italy ", "USA", "Cote d'ivoire"]
```

We can easily resolve these names to a standard format such as ISO3 codes 

```python
resolved_countries = places.resolve(countries, to_type="iso3_code")

print(resolved_countries)
# Output:
# ['ZWE', 'ITA', 'USA', 'CIV']
```

This works with pandas DataFrames too.

```python title="Resolving places in pandas DataFrames"
import pandas as pd

df = pd.DataFrame({"country": countries})

# Add the ISO3 codes to the DataFrame
df["iso3_code"] = places.resolve(df["country"], to_type="iso3_code")


print(df)
# Output:
#       country         iso3_code
# 0     zimbabwe        ZWE
# 1     Italy           ITA
# 2     USA             USA
# 3     Cote d'ivoire   CIV
```

## Filter places

Let's say that we are only interested in countries in Africa. It is easy to filter our countries with the
`filter_places` function.

```python title="Filter for African countries"
african_countries = places.filter(countries,
                                  filters={"region": "Africa"})

print(african_countries)
# Output:
# ['zimbabwe', "Cote d'ivoire"]
```

## Get places

We don't always want to resolve or standardize places. Sometimes we simple want to know what places belong to a 
particular category. For example we might want to know what countries in Africa are classified as upper income

```python
ui_africa = places.get_places(filters={"region": "Africa", 
                                       "income_level": ["Upper middle income", 
                                                        "High income"]}, 
                              place_format="name_short"
                              )

print(ui_africa)
# Output:
# ['Algeria', 'Botswana', 'Equatorial Guinea', 'Gabon', 'Libya',
# 'Mauritius', 'Namibia', 'Seychelles', 'South Africa']
```

The next pages will explore in more detail all the functionality and customizability of `bblocks-places`

