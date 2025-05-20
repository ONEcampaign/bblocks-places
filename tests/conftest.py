import sys
import types
import importlib.util
from pathlib import Path

# Stub pandas module with minimal functionality
pd_stub = types.ModuleType('pandas')
class Series(list):
    def map(self, func):
        return Series([func(x) for x in self])
    def unique(self):
        seen = []
        for x in self:
            if x not in seen:
                seen.append(x)
        return seen
pd_stub.Series = Series
pd_stub.DataFrame = type('DataFrame', (), {})
pd_stub.read_csv = lambda *a, **k: pd_stub.DataFrame()
sys.modules['pandas'] = pd_stub

# Dummy Data Commons client implementation
class DummyResponse:
    def __init__(self, data):
        self._data = data
    def to_flat_dict(self):
        return self._data
    def get_properties(self):
        return self._data

class DummyResolve:
    def __init__(self):
        self.mapping = {}
    def fetch_dcids_by_name(self, entities, entity_type):
        if isinstance(entities, str):
            entities = [entities]
        return DummyResponse({e: self.mapping.get(e) for e in entities})

class DummyNode:
    def __init__(self):
        self.mapping = {}
    def fetch_property_values(self, dcids, prop):
        return DummyResponse({d: self.mapping.get(d) for d in dcids})

class DummyClient:
    def __init__(self, **kwargs):
        self.resolve = DummyResolve()
        self.node = DummyNode()

dc_stub = types.ModuleType('datacommons_client')
dc_stub.DataCommonsClient = DummyClient
sys.modules['datacommons_client'] = dc_stub

# Load package modules without executing original __init__
PACKAGE_ROOT = Path(__file__).resolve().parents[1] / 'src' / 'bblocks' / 'places'

bblocks_pkg = types.ModuleType('bblocks')
bblocks_pkg.__path__ = [str(PACKAGE_ROOT.parent)]
sys.modules['bblocks'] = bblocks_pkg
places_pkg = types.ModuleType('bblocks.places')
places_pkg.__path__ = [str(PACKAGE_ROOT)]
sys.modules['bblocks.places'] = places_pkg

for name in ['config', 'utils', 'concordance', 'disambiguator', 'resolver']:
    spec = importlib.util.spec_from_file_location(f'bblocks.places.{name}', PACKAGE_ROOT / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[f'bblocks.places.{name}'] = module
    spec.loader.exec_module(module)

# expose helpers
pytest_plugins = []
