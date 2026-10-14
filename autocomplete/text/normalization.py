"""Utilidades de normalización de texto."""

from __future__ import annotations

import unicodedata


def strip_accents(text: str) -> str:
    """Elimina diacríticos (acentos, tildes, diéresis, virgulillas) de un texto.

    Ejemplos:
        >>> strip_accents("café")
        'cafe'
        >>> strip_accents("Árbol")
        'Arbol'
        >>> strip_accents("pingüino")
        'pinguino'
        >>> strip_accents("señor")
        'senor'
    """
    if not text:
        return text
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalize_key(text: str, remove_accents: bool = True) -> str:
    """Normaliza texto para ser usado como clave de búsqueda.

    Args:
        text: Texto a normalizar.
        remove_accents: Si ``True``, elimina acentos. Siempre pasa a minúsculas.

    Returns:
        Texto normalizado.
    """
    if not text:
        return text
    result = text.lower()
    if remove_accents:
        result = strip_accents(result)
    return result
