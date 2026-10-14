"""Fixtures compartidos por todos los tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from autocomplete import Autocomplete, Storage


@pytest.fixture
def ac_basico() -> Autocomplete:
    """Autocompletador con un set pequeño de palabras sin acentos."""
    return Autocomplete(["casa", "casamiento", "casco", "perro", "pez"])


@pytest.fixture
def ac_vacio() -> Autocomplete:
    """Autocompletador vacío."""
    return Autocomplete()


@pytest.fixture
def ac_acentos() -> Autocomplete:
    """Autocompletador con palabras con acentos."""
    return Autocomplete(["café", "cafetería", "cama", "árbol", "señor"])


@pytest.fixture
def tmp_sqlite(tmp_path: Path):
    """Storage sobre un archivo SQLite temporal."""
    url = f"sqlite:///{tmp_path / 'test.db'}"
    storage = Storage(url)
    try:
        yield storage
    finally:
        storage.close()


@pytest.fixture
def tmp_sqlite_mem():
    """Storage sobre SQLite en memoria."""
    storage = Storage("sqlite:///:memory:")
    try:
        yield storage
    finally:
        storage.close()
