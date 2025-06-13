"""Utility functions"""

import unicodedata
import string


def clean_string(s: str | None) -> str | None:
    """Cleans a string by:
    - Lowercasing
    - Removing all whitespace
    - Converting accented characters to their closest ASCII equivalent

    Args:
        s: Input string.

    Returns:
       Cleaned string.
    """

    if s is None:
        return None

    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(
        c
        for c in s
        if not unicodedata.combining(c)
        and c not in string.punctuation
        and not c.isspace()
    )
    return s


def split_list(lst, chunk_size):
    """Split a list into chunks of a specified size.

    Args:
        lst: The list to split.
        chunk_size: The size of each chunk.

    Yields:
        Chunks of the list.
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]
