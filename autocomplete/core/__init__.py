"""Núcleo del autocompletador: Trie, motor y similitud."""

from .engine import Autocomplete
from .similarity import damerau_levenshtein, find_similar, levenshtein
from .stats import LoadDirStats, LoadStats
from .trie import Trie, TrieNode

__all__ = [
    "Autocomplete",
    "LoadStats",
    "LoadDirStats",
    "Trie",
    "TrieNode",
    "levenshtein",
    "damerau_levenshtein",
    "find_similar",
]
