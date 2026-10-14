"""Excepciones personalizadas del módulo autocomplete."""


class AutocompleteError(Exception):
    """Excepción base del módulo autocomplete."""


class InvalidWordError(AutocompleteError):
    """Se lanza cuando una palabra no es válida."""


class InvalidPrefixError(AutocompleteError):
    """Se lanza cuando un prefijo no es válido."""
