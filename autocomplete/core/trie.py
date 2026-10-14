"""Implementación interna del Trie usada por el autocompletador."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterator, Optional

from ..text.normalization import normalize_key


@dataclass
class TrieNode:
    """Nodo de un Trie.

    Attributes:
        children: Mapa carácter normalizado -> nodo hijo.
        words: Mapa palabra original -> frecuencia.
    """

    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    words: Dict[str, int] = field(default_factory=dict)

    @property
    def is_end(self) -> bool:
        """Indica si el nodo representa el final de al menos una palabra."""
        return bool(self.words)


class Trie:
    """Trie con soporte de frecuencia y normalización de acentos.

    Las claves de navegación se normalizan (minúsculas y sin acentos) para
    permitir búsquedas insensibles a tildes y mayúsculas. La palabra
    original se preserva en ``TrieNode.words`` para devolverla tal cual.
    """

    def __init__(self, remove_accents: bool = True) -> None:
        self._root = TrieNode()
        self._remove_accents = remove_accents

    @property
    def root(self) -> TrieNode:
        return self._root

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _key(self, text: str) -> str:
        return normalize_key(text, remove_accents=self._remove_accents)

    # ------------------------------------------------------------------ #
    # Operaciones
    # ------------------------------------------------------------------ #
    def insert(self, word: str, weight: int = 1) -> None:
        """Inserta una palabra con un peso (frecuencia).

        Args:
            word: Palabra a insertar (se preserva tal cual).
            weight: Peso asociado. Debe ser mayor que 0.
        """
        if not word:
            return

        node = self._root
        for char in self._key(word):
            node = node.children.setdefault(char, TrieNode())

        node.words[word] = node.words.get(word, 0) + weight

    def find_node(self, prefix: str) -> Optional[TrieNode]:
        """Retorna el nodo final del prefijo normalizado, o ``None``."""
        node = self._root
        for char in self._key(prefix):
            node = node.children.get(char)
            if node is None:
                return None
        return node

    def contains(self, word: str) -> bool:
        """Indica si la palabra exacta existe en el Trie."""
        node = self.find_node(word)
        return node is not None and word in node.words

    def remove(self, word: str) -> bool:
        """Elimina una palabra. Retorna ``True`` si existía."""
        path = []
        node = self._root

        for char in self._key(word):
            child = node.children.get(char)
            if child is None:
                return False
            path.append((node, char))
            node = child

        if word not in node.words:
            return False

        del node.words[word]

        # Poda de nodos vacíos
        for parent, char in reversed(path):
            child = parent.children[char]
            if not child.words and not child.children:
                del parent.children[char]
            else:
                break

        return True

    def iter_words(self, node: Optional[TrieNode] = None) -> Iterator[str]:
        """Itera todas las palabras bajo un nodo (DFS iterativo)."""
        if node is None:
            node = self._root

        stack = [node]
        while stack:
            current = stack.pop()
            yield from current.words.keys()
            stack.extend(current.children.values())