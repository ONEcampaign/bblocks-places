# Why `bblocks-places`

Working with geographic data is a common headache for data analysts/engineers/researchers especially in
international development organisations. 

There are many great libraries that facilitate this work including:

- [country_converter](https://github.com/IndEcol/country_converter): versatile regex conversions for countries to different formats
- [pycountry](https://github.com/pycountry/pycountry): access to detailed ISO metadata on countries and languages
- [iso3166](https://github.com/deactivated/python-iso3166): direct access to ISO 3166 country codes.
- [HDX Python Country Library](https://github.com/OCHA-DAP/hdx-python-country/): provides country mappings including ISO 2, ISO 3 codes, and regions using live official data from the UN OCHA

`bblocks-places` adds to the strength of this ecosystem by offering a tool designed for accuracy,
flexibility, and extensibility.

## Accurate and transparent disambiguation

One of the core challenges in resolving place names is ambiguity. 
A name like "Congo" might refer to either the Republic of the Congo or the Democratic 
Republic of the Congo. "Georgia" could indicate the U.S. state or the independent country. 
"Ivory Coast" might also appear as "Côte d’Ivoire", depending on the source.

Different tools address disambiguation in various ways—often relying on techniques like 
regular expressions or fuzzy matching. However, these methods are not foolproof: 
they can miss valid matches or return incorrect ones. Analysts must remain vigilant 
when working with ambiguous or inconsistently labeled geographic data.

`bblocks-places` helps address this problem by flagging unresolved or ambiguous cases. 
When multiple possible matches exist, the tool surfaces all candidates to the user
and gives you control over how to handle them.

__No matches?__ → Choose to raise an error, return None, or provide a fallback value.

__Multiple matches?__ → Choose to raise an error, select the most likely candidate, 
or return all possible matches.

This explicit and flexible handling makes disambiguation transparent, auditable, 
and user-controlled.

## Broad support for many types of places

Most datasets focus on country-level data. `bblocks-places` offers extensive support 
to work with country-level data by default, allowing easy resolution and standardization of
country names, mapping to different formats, and grouping countries according to different
categories like regions and income level.

Beyond that, `bblocks-places` can be used to work with other place types like provinces,
countries, cities and any other place in the Data Commons knowledge graph. 
This flexibility allows you to work seamlessly across geographic levels and extend 
support to new or custom place types.

## Customizable concordance

`bblocks-places` uses a custom concordance table and custom mappings based on the 
UN's [M49 list](https://unstats.un.org/unsd/methodology/m49/) of countries and 
the [World Bank's income groups](https://datahelpdesk.worldbank.org/knowledgebase/articles/906519-world-bank-country-and-lending-groups) 
to easily resolve and
standardize places out of the box. You can also customize this by using your own
concordance table to override and extend mappings. This flexibility
ensures you are not locked in to the default mappings and you can adapt and build on the
package based on your specific requirements and data.



## Limitations

While `bblocks-places` offers broad and flexible support for resolving place names, 
it does come with a few constraints.

The primary limitation is its dependence on the Data Commons API for resolving places. 
This means an active internet connection is required to perform place lookups. In environments 
with limited or unstable connectivity—or when working with large datasets containing many unique 
places—this dependency can introduce latency due to the volume of API requests.

These limitations were known and carefully considered in the design of the package, and we’ve taken steps 
to minimize their impact as much as possible. Future enhancements may include features like offline resolution
and caching to further improve performance and usability in constrained environments.


