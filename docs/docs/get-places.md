# Get places

Sometimes you want to know what places belong to a particular category, rather than resolving or filtering
places. `bblocks-places` makes it easy to get list of places that fit different categories.

For example, you want to know what countries are official UN member states or all African countries. You can use the
`get_places` function to do this.

```python title="Get all African countries and territories"
african_countries = places.get_places({"region": "Africa"}, place_format="name_official")

print(african_countries)
# Output:
# ['Algeria', 'Angola', 'Benin', 'Botswana', 'British Indian Ocean Territory', 'Burkina Faso', .... ]
```

You may have noticed that the previous example contains some countries and some territories (such as 
British Indian Ocean Territory). The default concordance table used maps countries to different formats
according to those available in the M49 list of countries and some additional countries/territories such as
Taiwan. To see the full concordance table as a pandas DataFrame use the `get_default_concordance_table` function.

```python
df = places.get_default_concordance_table()
```

You can also get places that fit into multiple categories. Using the previous example, let's say we want all African
countries that are UN member states.

```python
africa_un_members = places.get_places({"region": "Africa", "un_member": True}, 
                                      place_format="name_official")

print(africa_un_members)
# Output:
# # ['Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', .... ]
```

The entire list of filters available is:

- `region` - UN region name
- `region_code` - UN region code
- `subregion` - UN subregion
- `subregion_code` - UN subregion code
- `intermediate_region_code` - UN intermediate region code
- `intermediate_region` - UN intermediate region name
- `income_level` - World Bank income level
- `m49_member` - M49 country list member (True if member)
- `ldc` - Less developed country
- `lldc` - Land locked less developed country
- `sids` - Small Island Developing State
- `un_member` - UN official member
- `un_observer` - UN observer state
- `un_former_member` - UN former member state

## Convenience functions

Several convenience functions exist to get places for common categories:

- `get_un_members` - get all official UN members
- `get_un_observers` - get all UN observer states
- `get_m49_places` - get all M49 places
- `get_sids` - get all Small Island Developing States
- `get_ldc` - get all Least Developed Countries
- `get_lldc` - get all Landlocked Developing Countries
- `get_african_countries` - get all African countries

