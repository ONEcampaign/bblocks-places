# Filter places

Filtering places based on some categories like region or income level is easy with `bblocks-places`.

## Basic filtering

Let's say we have a list of countries

```python
countries = ["Zimbabwe", "Italy", "Botswana", "United States"]
```

You can filter these countries using the `filter` function. For example, let's filter
for countries in Africa.

```python
african_countries = places.filter_places(countries, filters={"region": "Africa"})

print(african_countries)
# Output:
# ['Zimbabwe', 'Botswana']
```

## Filter for multiple categories

You can filter for multiple categories. For example, let's filter for lower middle income countries in Africa.

```python
lmic_africa = places.filter_places(countries,
                                   filters={"region": "Africa",
                                            "income_level": "Lower middle income"})

print(lmic_africa)
# Output:
# ['Zimbabwe']
```

## Handling empty filter results

When applying filters, it's possible that no places match the specified criteria.
In such cases, bblocks-places returns an empty list or Series by default and logs a 
clear warning to alert the user.

For example let's filter for high income countries in Africa.

```python
hic_africa = places.filter_places(countries,
                                  filters={"region": "Africa",
                                           "income_level": "High income"})

print(hic_africa)
# Output:
# WARNING: No places found for filters {'region': ['Africa'], 'income_level': ['High income']}
# []
```

You can also choose to raise an error when no places match the filter criteria by setting the `raise_if_empty`
parameter to `True`.

```python
hic_africa = places.filter_places(countries,
                                  filters={"region": "Africa",
                                           "income_level": "High income"})

# Output:
# ValueError: No places found for filters {'region': ['Africa'], 'income_level': ['High income']}
```

## Helper functions

Additional convenience functions exist for common filtering operations:

- `filter_african_countries` - Filter a list or Series for African countries

















