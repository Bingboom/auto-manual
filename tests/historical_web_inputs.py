"""Supply declared historical shared inputs during immutable-edition tests.

These fixtures are exact, hash-checked repository bytes, never reconstructed
goldens. Current-style tests continue to read the current contracts. Source
and artwork mutations under temporary package roots remain visible.
"""
from contextlib import contextmanager
from functools import wraps
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from unittest import mock

from tools.web.presentation_contract import _load_cached

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures/historical_web_inputs"


def historical_inputs() -> dict[Path, bytes]:
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    inputs = {}
    for row in manifest["inputs"]:
        data = (FIXTURES / row["fixture"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise AssertionError(f"historical dependency changed: {row['fixture']}")
        inputs[(ROOT / row["repository_path"]).resolve()] = data
    return inputs


@contextmanager
def historical_repository_inputs():
    inputs = historical_inputs()
    original_open = Path.open

    def open_at(path, mode="r", *args, **kwargs):
        source = (FIXTURES / path.name if mode in ("r", "rb", "rt")
                  and path.resolve() in inputs else path)
        return original_open(source, mode, *args, **kwargs)

    _load_cached.cache_clear()
    try:
        with mock.patch.object(Path, "open", open_at):
            yield
    finally:
        _load_cached.cache_clear()


def historical_shared_inputs(cls):
    """Scope historical dependencies to each method of a legacy TestCase."""
    def decorate(test):
        @wraps(test)
        def run(*args, **kwargs):
            with historical_repository_inputs():
                return test(*args, **kwargs)
        return run

    for name, test in list(vars(cls).items()):
        if name.startswith("test_") and callable(test):
            setattr(cls, name, decorate(test))
    return cls


@contextmanager
def temporary_derivation(module):
    """Replay derivation without writing into an approved source package."""
    with tempfile.TemporaryDirectory() as temp:
        destination = Path(temp).resolve() / module.PACKAGE.name
        shutil.copytree(module.PACKAGE, destination, ignore=shutil.ignore_patterns("__pycache__"))
        with mock.patch.object(module, "PACKAGE", destination):
            yield destination
