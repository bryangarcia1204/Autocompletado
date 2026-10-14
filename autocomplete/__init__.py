"""Módulo de autocompletado, autocorrección y sugerencia de comandos.

Uso básico:
    from autocomplete import Autocomplete

    ac = Autocomplete(["casa", "casamiento", "casco"])
    print(ac.suggestions("cas"))

Carga masiva:
    from autocomplete import Autocomplete

    ac = Autocomplete.from_file("palabras.txt")
    ac = Autocomplete.from_file("palabras.tsv", separator="\\t")
    ac = Autocomplete.from_file("palabras.txt.gz")

Autocorrección:
    ac.correct("casaa")   # [('casa', 1), ...]

CLI:
    python -m autocomplete -h
"""

from .config import Config
from .core import (Autocomplete, LoadDirStats, LoadStats, Trie, TrieNode,
                   damerau_levenshtein, find_similar, levenshtein)
from .exceptions import AutocompleteError, InvalidPrefixError, InvalidWordError
from .execution import ExecutionResult, run_command
from .storage import Base, HistoryRecord, PreferenceRecord, Storage, WordRecord
from .text import normalize_key, strip_accents

__all__ = [
    # Núcleo
    "Autocomplete",
    "LoadStats",
    "LoadDirStats",
    "Trie",
    "TrieNode",
    # Similitud
    "levenshtein",
    "damerau_levenshtein",
    "find_similar",
    # Texto
    "strip_accents",
    "normalize_key",
    # Persistencia
    "Storage",
    "Base",
    "WordRecord",
    "HistoryRecord",
    "PreferenceRecord",
    # Configuración
    "Config",
    # Ejecución
    "ExecutionResult",
    "run_command",
    # Excepciones
    "AutocompleteError",
    "InvalidPrefixError",
    "InvalidWordError",
]

__version__ = "1.0.0"
