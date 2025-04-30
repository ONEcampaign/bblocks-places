""" " """

import sys
import unicodedata
import string

# All accents
_REMOVE = {c: None for c in range(sys.maxunicode) if unicodedata.combining(chr(c))}

# All punctuation and whitespace
for ch in string.punctuation + string.whitespace:
    _REMOVE[ord(ch)] = None


def flatten_dict(d: dict[str : list[str, None]]) -> dict[str, str | None | list[str]]:
    """Take a dictionary with values as a list and flatten it.

    - If the list is empty, set the value to None
    - If there are null values in the list, remove them
    """

    # if the dictionary is empty, return an empty dictionary
    if not d:
        return {}

    # loop through the dictionary
    for k, v in d.items():

        # remove any duplicates from the list (in place)
        if isinstance(v, list):
            d[k] = [i for i in list(dict.fromkeys(v)) if i]

        # check if the list is empty
        if not v:
            d[k] = None

        # if there is only 1 value, return it as a string
        if isinstance(v, list) and len(v) == 1:
            d[k] = v[0]

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

    return {k: [dict2[id_] for id_ in v if id_ in dict2] for k, v in dict1.items()}


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
    return unicodedata.normalize("NFKD", s.casefold()).translate(_REMOVE)


def split_list(lst, chunk_size):
    """Split a list into chunks of a specified size."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]
