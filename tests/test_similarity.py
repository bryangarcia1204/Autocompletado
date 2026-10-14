"""Tests de las funciones de similitud entre cadenas."""

from __future__ import annotations

from autocomplete import damerau_levenshtein, find_similar, levenshtein


class TestLevenshtein:
    def test_identicas(self) -> None:
        assert levenshtein("casa", "casa") == 0

    def test_vacia(self) -> None:
        assert levenshtein("", "") == 0
        assert levenshtein("abc", "") == 3
        assert levenshtein("", "abc") == 3

    def test_sustitucion(self) -> None:
        assert levenshtein("casa", "caza") == 1

    def test_insercion(self) -> None:
        assert levenshtein("casa", "casaa") == 1

    def test_borrado(self) -> None:
        assert levenshtein("casa", "csa") == 1

    def test_max_dist_corta_temprano(self) -> None:
        # Cuando la distancia supera el umbral devuelve max_dist + 1
        resultado = levenshtein("abc", "xyz", max_dist=1)
        assert resultado > 1


class TestDamerauLevenshtein:
    def test_identicas(self) -> None:
        assert damerau_levenshtein("casa", "casa") == 0

    def test_transposicion(self) -> None:
        # La transposición cuenta como 1 (no como 2)
        assert damerau_levenshtein("casa", "csaa") == 1

    def test_igual_que_levenshtein_sin_transposicion(self) -> None:
        assert damerau_levenshtein("casa", "caza") == 1

    def test_max_dist(self) -> None:
        resultado = damerau_levenshtein("abc", "xyz", max_dist=1)
        assert resultado > 1


class TestFindSimilar:
    def test_basico(self) -> None:
        candidatos = ["casa", "caso", "perro", "pez"]
        resultado = find_similar("csa", candidatos, max_distance=2)
        palabras = [w for w, _ in resultado]
        assert "casa" in palabras

    def test_limit(self) -> None:
        candidatos = ["casa", "caso", "casco", "casona"]
        resultado = find_similar("casa", candidatos, limit=2)
        assert len(resultado) == 2

    def test_orden_por_distancia(self) -> None:
        candidatos = ["casa", "casco", "casamiento"]
        resultado = find_similar("casa", candidatos, max_distance=10)
        distancias = [d for _, d in resultado]
        assert distancias == sorted(distancias)

    def test_sin_candidatos(self) -> None:
        assert find_similar("xyz", [], max_distance=2) == []

    def test_ignora_acentos(self) -> None:
        resultado = find_similar("cafe", ["café", "casa"], max_distance=1)
        palabras = [w for w, _ in resultado]
        assert "café" in palabras

    def test_sin_transposicion(self) -> None:
        # Con use_transposition=False, "csa" -> "casa" es distancia 1
        # igual, pero probamos que la opción es aceptada
        resultado = find_similar("casa", ["casa"], use_transposition=False)
        assert resultado == [("casa", 0)]
