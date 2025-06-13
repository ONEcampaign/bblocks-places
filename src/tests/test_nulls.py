import pandas as pd
import pytest

from bblocks.places.main import resolve, resolve_map


def test_resolve_ignores_nulls_series():
    data = pd.Series(["ITA", pd.NA, "AFG"])
    result = resolve(data, from_type="iso3_code", to_type="iso2_code")
    assert list(result) == ["IT", pd.NA, "AF"]


def test_resolve_raises_on_nulls_when_disabled():
    data = pd.Series(["ITA", pd.NA])
    with pytest.raises(ValueError):
        resolve(data, from_type="iso3_code", to_type="iso2_code", ignore_nulls=False)


def test_resolve_map_ignores_nulls():
    mapping = resolve_map(["ITA", None], from_type="iso3_code", to_type="iso2_code")
    assert mapping == {"ITA": "IT"}
