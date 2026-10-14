"""Módulo de autocompletado, autocorrección y sugerencia de comandos.

Uso básico:
    from autocomplete import Autocomplete

    ac = Autocomplete(["casa", "casamiento", "casco"])
    print(ac.suggestions("cas"))

CLI:
    python -m autocomplete -h
"""

from .config import Config
from .core import Autocomplete, LoadDirStats, LoadStats
from .exceptions import AutocompleteError, InvalidPrefixError, InvalidWordError
from .execution import ExecutionResult, run_command
from .storage import Storage
from .text import normalize_key, strip_accents

__all__ = [
    "Autocomplete",
    "LoadStats",
    "LoadDirStats",
    "Config",
    "Storage",
    "ExecutionResult",
    "run_command",
    "strip_accents",
    "normalize_key",
    "AutocompleteError",
    "InvalidPrefixError",
    "InvalidWordError",
]

__version__ = "1.5.0"