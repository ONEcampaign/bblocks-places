"""Tests for the utils module"""

import pytest

from bblocks_places import utils

@pytest.mark.parametrize("input_str, expected", [
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
])
def test_simple_clean_string(input_str, expected):
    assert utils.clean_string(input_str) == expected