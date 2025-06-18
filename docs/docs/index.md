# `bblocks-places`

__Resolve and standardize places and work with political and geographic groupings.__

[![GitHub Repo](https://img.shields.io/badge/GitHub-bblocks_places-181717?style=flat-square&labelColor=%23ddd&logo=github&color=%23555&logoColor=%23000)](https://github.com/ONEcampaign/bblocks-places)
[![GitHub License](https://img.shields.io/github/license/ONEcampaign/bblocks-places?style=flat-square&labelColor=%23ddd)](https://github.com/ONEcampaign/bblocks_places/blob/main/LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/bblocks_places?style=flat-square&labelColor=%23ddd)](https://pypi.org/project/bblocks_places/)
[![Codecov](https://img.shields.io/codecov/c/github/ONEcampaign/bblocks-places?style=flat-square&labelColor=ddd)](https://codecov.io/gh/ONEcampaign/bblocks-places)


Working with country data can be tedious. One source calls it “_South Korea_” another 
says “_Republic of Korea_” a third uses “_KOR_” — and suddenly your analysis breaks and you spend
hours manually standardizing all the names. These inconsistencies are common in cross-geographic datasets and can lead to data 
cleaning headaches, merge errors, or misleading conclusions.

`bblocks-places` eliminates this hassle by offering a simple, reliable interface to resolve, standardize, 
and work with country, region, and other place names. 

__Key features__:

- Disambiguate and standardize free-text country names (e.g. "Ivory Coast" → “Côte d’Ivoire”)
- Convert between place formats like ISO codes and official names
- Filter and retrieve countries by attributes like region, income group, or UN membership
- Customize resolution logic with your own concordance or override mappings


__Built on top of Google's [Data Commons](https://datacommons.org/)__, 
an open knowledge graph integrating public data from the UN, World Bank, and more.
