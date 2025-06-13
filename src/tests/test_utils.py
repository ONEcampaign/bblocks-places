"""Tests for the utils module"""

import pytest

from bblocks.places import utils


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("Côte d'Ivoire", "cotedivoire"),
        ("São Tomé and Príncipe", "saotomeandprincipe"),
        ("  Hello World  ", "helloworld"),
        ("\nNew\nLine\tTab ", "newlinetab"),
        ("École", "ecole"),
        ("naïve café", "naivecafe"),
        ("Ångström", "angstrom"),
        ("", ""),  # Empty string
        ("    ", ""),  # Only spaces
        ("12345", "12345"),  # Numbers should stay
        (None, None),  # None input should return None
    ],
)
def test_simple_clean_string(input_str, expected):
    """Test the clean_string function with various inputs."""

    assert utils.clean_string(input_str) == expected


@pytest.mark.parametrize(
    "input_str, expected",
    [
        # Non‐Latin characters should be preserved
        ("漢字", "漢字"),

        # Combining marks only get stripped out entirely
        ("\u0301\u0300", ""),
    ],
)
def test_clean_string_non_latin_and_combining(input_str, expected):
    """Test the clean_string function with non-Latin characters and combining marks."""
    assert utils.clean_string(input_str) == expected



@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("co-operation",      "cooperation"),   # hyphen
        ("end_to_end",        "endtoend"),      # underscore
        ("[brackets]",        "brackets"),      # square braces
        ("{curly}",           "curly"),         # curly braces
    ],
)
def test_clean_string_various_punctuation(input_str, expected):
    """Test the clean_string function with various punctuation."""
    assert utils.clean_string(input_str) == expected


@pytest.mark.parametrize(
    "lst, chunk_size, expected",
    [
        ([], 3, []),                             # empty list
        ([1, 2, 3, 4], 2, [[1, 2], [3, 4]]),     # exact multiple
        ([1, 2, 3, 4, 5], 2, [[1, 2], [3, 4], [5]]),  # remainder at end
        ([1, 2, 3], 1, [[1], [2], [3]]),         # singleton chunks
        ([1, 2], 5, [[1, 2]]),                   # chunk size larger than list
    ],
)
def test_split_list_various(lst, chunk_size, expected):
    """Test the split_list function with various inputs."""
    assert list(utils.split_list(lst, chunk_size)) == expected


def test_split_list_zero_chunk_size():
    """Test that split_list raises ValueError for zero chunk size."""
    with pytest.raises(ValueError):
        # range(step=0) should trigger ValueError
        list(utils.split_list([1, 2, 3], 0))


def test_split_list_negative_chunk_size():
    """Test that split_list returns an empty list for negative chunk size."""
    # negative step yields no iterations
    assert list(utils.split_list([1, 2, 3], -1)) == []