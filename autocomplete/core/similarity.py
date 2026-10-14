"""Funciones de similitud entre cadenas.

Incluye distancia de Levenshtein y Damerau-Levenshtein (esta última
cuenta las transposiciones como una sola edición, ideal para typos
del tipo "gti" -> "git").
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from ..text.normalization import strip_accents


def levenshtein(a: str, b: str, max_dist: Optional[int] = None) -> int:
    """Distancia de Levenshtein clásica.

    Args:
        a: Primera cadena.
        b: Segunda cadena.
        max_dist: Si se especifica, corta temprano cuando la distancia
            supera este umbral (devuelve ``max_dist + 1``).
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if max_dist is not None and abs(len(a) - len(b)) > max_dist:
        return max_dist + 1

    if len(a) > len(b):
        a, b = b, a

    prev = list(range(len(a) + 1))
    for i, cb in enumerate(b, start=1):
        curr = [i]
        for j, ca in enumerate(a, start=1):
            cost = 0 if ca == cb else 1
            curr.append(
                min(
                    curr[j - 1] + 1,  # inserción
                    prev[j] + 1,  # borrado
                    prev[j - 1] + cost,  # sustitución
                )
            )
        prev = curr
        if max_dist is not None and min(curr) > max_dist:
            return max_dist + 1
    return prev[-1]


def damerau_levenshtein(a: str, b: str, max_dist: Optional[int] = None) -> int:
    """Distancia Damerau-Levenshtein (incluye transposiciones)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if max_dist is not None and abs(len(a) - len(b)) > max_dist:
        return max_dist + 1

    len_a, len_b = len(a), len(b)
    d = [[0] * (len_b + 1) for _ in range(len_a + 1)]

    for i in range(len_a + 1):
        d[i][0] = i
    for j in range(len_b + 1):
        d[0][j] = j

    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,
                d[i][j - 1] + 1,
                d[i - 1][j - 1] + cost,
            )
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)

    return d[len_a][len_b]


def _normalize(text: str, ignore_accents: bool, ignore_case: bool) -> str:
    if ignore_case:
        text = text.lower()
    if ignore_accents:
        text = strip_accents(text)
    return text


def find_similar(
    word: str,
    candidates: Iterable[str],
    max_distance: int = 2,
    limit: Optional[int] = 5,
    ignore_accents: bool = True,
    ignore_case: bool = True,
    use_transposition: bool = True,
) -> List[Tuple[str, int]]:
    """Devuelve los candidatos más parecidos a ``word``.

    Returns:
        Lista de ``(palabra, distancia)`` ordenada por distancia ascendente
        y, en empate, alfabéticamente.
    """
    key = _normalize(word, ignore_accents, ignore_case)
    dist_fn = damerau_levenshtein if use_transposition else levenshtein

    results: List[Tuple[str, int]] = []
    for cand in candidates:
        ckey = _normalize(cand, ignore_accents, ignore_case)
        dist = dist_fn(key, ckey, max_dist=max_distance)
        if dist <= max_distance:
            results.append((cand, dist))

    results.sort(key=lambda t: (t[1], t[0].lower()))
    return results[:limit] if limit is not None else results
