import os
from pathlib import Path
import sys
import types
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Prepare stub packages
core_stub = types.ModuleType("dumpsleuth.core")
core_stub.__path__ = [str(SRC / "dumpsleuth" / "core")]

base_stub = types.ModuleType("dumpsleuth")
base_stub.__path__ = [str(SRC / "dumpsleuth")]
base_stub.core = core_stub
sys.modules['dumpsleuth'] = base_stub
sys.modules['dumpsleuth.core'] = core_stub

# Stub config module
config_stub = types.ModuleType("dumpsleuth.core.config")
class Config(dict):
    def get(self, key, default=None):
        if key in ('analysis.max_file_size', 'analysis.mmap_threshold'):
            return '1048576'
        if key == 'analysis.use_mmap':
            return False
        return default

    @classmethod
    def from_file(cls, path):
        return cls()

def get_default_config():
    return Config()
config_stub.Config = Config
config_stub.get_default_config = get_default_config
sys.modules['dumpsleuth.core.config'] = config_stub

# Load plugin and parser modules
for name in ['plugin', 'parser']:
    spec = importlib.util.spec_from_file_location(
        f'dumpsleuth.core.{name}', SRC / 'dumpsleuth' / 'core' / f'{name}.py'
    )
    module = importlib.util.module_from_spec(spec)
    module.__package__ = 'dumpsleuth.core'
    spec.loader.exec_module(module)
    sys.modules[f'dumpsleuth.core.{name}'] = module

# Stub extractor modules used by analyzer
extractor_names = {
    'strings_plugin': 'StringsExtractorPlugin',
    'network': 'NetworkExtractorPlugin',
    'registry': 'RegistryExtractorPlugin',
    'processes': 'ProcessExtractorPlugin',
}
for mod_name, cls_name in extractor_names.items():
    mod = types.ModuleType(f'dumpsleuth.extractors.{mod_name}')
    class Dummy:
        def get_name(self):
            return cls_name
        def analyze(self, *a, **k):
            return {}
    setattr(mod, cls_name, Dummy)
    sys.modules[f'dumpsleuth.extractors.{mod_name}'] = mod

# Load analyzer module
spec = importlib.util.spec_from_file_location(
    'dumpsleuth.core.analyzer', SRC / 'dumpsleuth' / 'core' / 'analyzer.py'
)
analyzer_module = importlib.util.module_from_spec(spec)
analyzer_module.__package__ = 'dumpsleuth.core'
spec.loader.exec_module(analyzer_module)
analyzer_module.DumpAnalyzer._load_default_plugins = lambda self: None
DumpAnalyzer = analyzer_module.DumpAnalyzer


def test_get_dump_info(tmp_path):
    dump_path = tmp_path / 'sample.dmp'
    dump_path.write_bytes(b'MDMP' + b'\x00' * 64)
    analyzer = DumpAnalyzer(str(dump_path))
    info = analyzer.get_dump_info()
    assert info['format'] == 'minidump'
    assert info['file_name'] == dump_path.name
    assert info['file_size'] == os.path.getsize(dump_path)
