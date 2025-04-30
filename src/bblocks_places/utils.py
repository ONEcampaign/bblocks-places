"""" """

import unicodedata
import string


def _remove_duplicates_in_place(lst: list[str | list | None]) -> None:
    """Remove duplicate values from a list in-place, preserving order.
    Works with unhashable and nested items (e.g. lists, dicts).

    Args:
        lst: The list to remove duplicates from.

    Returns:
        None: The list is modified in-place.
    """
    seen = []
    for item in lst:
        if item not in seen:
            seen.append(item)
    lst[:] = seen


def flatten_dict(d: dict[str: list[str, None]]) -> dict[str, str | None | list[str]]:
    """Take a dictionary with values as a list and flatten it.

    - If the list is empty, set the value to None
    - If there are null values in the list, remove them
    """

    # if the dictionary is empty, return an empty dictionary
    if not d:
        return {}

    # loop through the dictionary
    for k, v in d.items():

        # remove any duplicates from the list
        _remove_duplicates_in_place(v)

        # check if there are any Nones in the list and remove them
        for i in v:
            if i is None:
                v.remove(i)

        # check if the list is empty
        if not v:
            d[k] = None

        # if there is only 1 value, return it as a string
        elif len(v) == 1:
            d[k] = v[0]

        # if there are multiple values, return it as a list
        elif len(v) > 1:
            d[k] = v

    return d


def map_dict(dict1: dict, dict2: dict) -> dict[str, list[str]]:
    """Map the values in s second dictionary to the values in the first dictionary where the
    values in the first dictionary are the keys in the second dictionary.

    e.g.
    dict1 ={
        'a': ['b', 'c'],
        'b': ['d', 'e']
    }

    dict2 = {
        'b': 'x',
        'c': 'y',
        'd': 'z'
    }

    map_dict(dict1, dict2) = {
        'a': ['x', 'y'],
        'b': ['z']
    }
    """

    return {
        k: [dict2[id_] for id_ in v if id_ in dict2]
        for k, v in dict1.items()
    }



def clean_string(s: str) -> str:
    """Cleans a string by:
    - Lowercasing
    - Removing all whitespace
    - Converting accented characters to their closest ASCII equivalent

    Args:
        s: Input string.

    Returns:
       Cleaned string.
    """

    s = s.lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = ''.join(c for c in s if c not in string.punctuation)
    s = ''.join(s.split())
    return s

def split_list(lst, chunk_size):
    """Split a list into chunks of a specified size."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]
