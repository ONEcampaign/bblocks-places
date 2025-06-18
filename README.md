# bblocks-places

__Resolve and standardize places and work with political and geographic groupings__

[![PyPI](https://img.shields.io/pypi/v/bblocks_places.svg)](https://pypi.org/project/bblocks_places/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bblocks_places.svg)](https://pypi.org/project/bblocks_places/)
[![Docs](https://img.shields.io/badge/docs-bblocks-blue)](https://docs.one.org/tools/bblocks/places/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/ONEcampaign/bblocks-places/graph/badge.svg?token=3ONEA8JQTC)](https://codecov.io/gh/ONEcampaign/bblocks-places)


Working with country data can be tedious. One source calls it “South Korea” another says 
“Republic of Korea” a third uses “KOR” — and suddenly your analysis breaks and you spend hours 
manually standardizing all the names. These inconsistencies are common in cross-geographic datasets 
and can lead to data cleaning headaches, merge errors, or misleading conclusions.

bblocks-places eliminates this hassle by offering a simple, reliable interface to resolve, 
standardize, and work with country, region, and other place names.

__Key features__:

- Disambiguate and standardize free-text country names (e.g. "Ivory Coast" → “Côte d’Ivoire”)
- Convert between place formats like ISO codes and official names
- Filter and retrieve countries by attributes like region, income group, or UN membership
- Customize resolution logic with your own concordance or override mappings 


Built on top of Google's [Data Commons](https://datacommons.org/), an open knowledge graph integrating public data from the
UN, World Bank, and more. `bblocks-places` is part of the bblocks ecosystem, 
a set of Python packages designed as building blocks for working with data in the international development 
and humanitarian sectors.

Read the [documentation](https://docs.one.org/tools/bblocks/places/)
for more details on how to use the package and the motivation for its creation.

## Installation

The package can be installed in various ways. 

```bash
pip install bblocks-places
```

Or install the main `bblocks` package with an extra:

```bash
pip install bblocks[places]
```

### Usage

Import the package and start resolving places:

```python
from bblocks import places
```

Lets start with a very simple example. Say we have a list of countries with non standard names

```python
countries = ["zimbabwe", " Italy ", "USA", "Cote d'ivoire"]
```

We can easily resolve these names to a standard format such as ISO3 codes

```python
resolved_countries = places.resolve_places(countries, to_type="iso3_code")

print(resolved_countries)
# Output:
# ['ZWE', 'ITA', 'USA', 'CIV']
```

This works with pandas DataFrames too.

```python title="Resolving places in pandas DataFrames"
import pandas as pd

df = pd.DataFrame({"country": countries})

# Add the ISO3 codes to the DataFrame
df["iso3_code"] = places.resolve_places(df["country"], to_type="iso3_code")

print(df)
# Output:
#       country         iso3_code
# 0     zimbabwe        ZWE
# 1     Italy           ITA
# 2     USA             USA
# 3     Cote d'ivoire   CIV
```

#### Filter places

Let's say that we are only interested in countries in Africa. It is easy to filter our countries with the
`filter_places` function.

```python title="Filter for African countries"
african_countries = places.filter_places(countries,
                                         filters={"region": "Africa"})

print(african_countries)
# Output:
# ['zimbabwe', "Cote d'ivoire"]
```

#### Get places

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

Visit the [documentation page](https://docs.one.org/tools/bblocks/places/) for the full package documentation and examples.

## Contributing
Contributions are welcome! Please see the
[CONTRIBUTING](https://github.com/ONEcampaign/bblocks-places/blob/main/CONTRIBUTING.md) 
page for details on how to get started, report bugs, fix issues, and submit enhancements.