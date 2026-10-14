"""Tests del núcleo: `Autocomplete`, `Trie` y `TrieNode`."""

from __future__ import annotations

import pytest

from autocomplete import Autocomplete, InvalidWordError
from autocomplete.core.trie import Trie, TrieNode


# ---------------------------------------------------------------------- #
# Autocomplete: sugerencias
# ---------------------------------------------------------------------- #
class TestSugerencias:
    def test_basicas(self, ac_basico: Autocomplete) -> None:
        assert ac_basico.suggestions("cas") == [
            "casa",
            "casamiento",
            "casco",
        ]

    def test_sin_coincidencias(self, ac_basico: Autocomplete) -> None:
        assert ac_basico.suggestions("zzz") == []

    def test_prefijo_vacio(self, ac_basico: Autocomplete) -> None:
        assert ac_basico.suggestions("") == []

    def test_limit(self, ac_basico: Autocomplete) -> None:
        assert ac_basico.suggestions("cas", limit=2) == [
            "casa",
            "casamiento",
        ]

    def test_orden_por_frecuencia(self) -> None:
        ac = Autocomplete()
        ac.add_word("casa", weight=1)
        ac.add_word("casamiento", weight=10)
        ac.add_word("casco", weight=5)
        assert ac.suggestions("cas") == [
            "casamiento",
            "casco",
            "casa",
        ]

    def test_orden_alfabetico(self) -> None:
        ac = Autocomplete()
        ac.add_word("casa", weight=1)
        ac.add_word("casamiento", weight=10)
        assert ac.suggestions("cas", sort_by_frequency=False) == [
            "casa",
            "casamiento",
        ]

    def test_preserva_mayusculas(self) -> None:
        ac = Autocomplete(["Casa", "casamiento"])
        assert "Casa" in ac.suggestions("cas")

    def test_prefijo_no_str(self, ac_basico: Autocomplete) -> None:
        with pytest.raises(Exception):
            ac_basico.suggestions(123)  # type: ignore[arg-type]


# ---------------------------------------------------------------------- #
# Autocomplete: add / remove / contains
# ---------------------------------------------------------------------- #
class TestAddRemove:
    def test_add_word_vacia(self, ac_vacio: Autocomplete) -> None:
        with pytest.raises(InvalidWordError):
            ac_vacio.add_word("")

    def test_add_word_espacios(self, ac_vacio: Autocomplete) -> None:
        with pytest.raises(InvalidWordError):
            ac_vacio.add_word("   ")

    def test_add_word_peso_invalido(self, ac_vacio: Autocomplete) -> None:
        with pytest.raises(InvalidWordError):
            ac_vacio.add_word("x", weight=0)

    def test_add_word_no_str(self, ac_vacio: Autocomplete) -> None:
        with pytest.raises(InvalidWordError):
            ac_vacio.add_word(None)  # type: ignore[arg-type]

    def test_add_dict(self, ac_vacio: Autocomplete) -> None:
        ac_vacio.add_words({"casa": 3, "casco": 1})
        assert ac_vacio.suggestions("cas") == ["casa", "casco"]

    def test_remove_word(self, ac_basico: Autocomplete) -> None:
        assert ac_basico.remove_word("casa") is True
        assert ac_basico.remove_word("casa") is False
        assert "casa" not in ac_basico.suggestions("cas")

    def test_contains(self, ac_basico: Autocomplete) -> None:
        assert ac_basico.contains("casa") is True
        assert ac_basico.contains("casaa") is False
        assert "casa" in ac_basico

    def test_contains_vacia(self, ac_basico: Autocomplete) -> None:
        assert ac_basico.contains("") is False

    def test_len(self, ac_basico: Autocomplete) -> None:
        assert len(ac_basico) == 5

    def test_all_words(self, ac_basico: Autocomplete) -> None:
        palabras = set(ac_basico.all_words())
        assert palabras == {"casa", "casamiento", "casco", "perro", "pez"}


# ---------------------------------------------------------------------- #
# Autocomplete: corrección
# ---------------------------------------------------------------------- #
class TestCorrect:
    def test_typo_simple(self, ac_basico: Autocomplete) -> None:
        resultados = ac_basico.correct("casaa", max_distance=1)
        assert ("casa", 1) in resultados

    def test_transposicion(self, ac_basico: Autocomplete) -> None:
        # "csa" -> "casa" requiere transposición (1 edición Damerau)
        resultados = ac_basico.correct("csa", max_distance=2)
        assert any(w == "casa" for w, _ in resultados)

    def test_sin_sugerencias(self, ac_basico: Autocomplete) -> None:
        resultados = ac_basico.correct("zzzzzzz", max_distance=1)
        assert resultados == []

    def test_correct_palabra_vacia(self, ac_basico: Autocomplete) -> None:
        with pytest.raises(InvalidWordError):
            ac_basico.correct("")

    def test_correct_limit(self, ac_basico: Autocomplete) -> None:
        resultados = ac_basico.correct("ca", max_distance=3, limit=1)
        assert len(resultados) == 1


# ---------------------------------------------------------------------- #
# Trie interno
# ---------------------------------------------------------------------- #
class TestTrie:
    def test_insert_y_contains(self) -> None:
        t = Trie()
        t.insert("hola")
        assert t.contains("hola") is True
        assert t.contains("adios") is False

    def test_insert_con_peso(self) -> None:
        t = Trie()
        t.insert("hola", weight=3)
        t.insert("hola", weight=2)
        node = t.find_node("hola")
        assert node is not None
        assert node.words["hola"] == 5

    def test_find_node_prefijo(self) -> None:
        t = Trie()
        t.insert("casamiento")
        node = t.find_node("cas")
        assert node is not None

    def test_find_node_inexistente(self) -> None:
        t = Trie()
        t.insert("casa")
        assert t.find_node("zz") is None

    def test_remove(self) -> None:
        t = Trie()
        t.insert("casa")
        assert t.remove("casa") is True
        assert t.remove("casa") is False
        assert t.contains("casa") is False

    def test_iter_words(self) -> None:
        t = Trie()
        for w in ["a", "ab", "abc", "b"]:
            t.insert(w)
        assert set(t.iter_words()) == {"a", "ab", "abc", "b"}

    def test_trie_node_is_end(self) -> None:
        node = TrieNode()
        assert node.is_end is False
        node.words["x"] = 1
        assert node.is_end is True

    def test_normalizacion_acentos(self) -> None:
        t = Trie()  # remove_accents=True por defecto
        t.insert("café")
        assert t.contains("café") is True
        # El nodo de "cafe" (sin tilde) existe
        assert t.find_node("cafe") is not None

    def test_sin_normalizacion(self) -> None:
        t = Trie(remove_accents=False)
        t.insert("café")
        assert t.find_node("cafe") is None
        assert t.find_node("café") is not None
