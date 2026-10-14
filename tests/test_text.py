"""Tests de normalización de texto."""

from __future__ import annotations

from autocomplete import normalize_key, strip_accents


class TestStripAccents:
    def test_basico(self) -> None:
        assert strip_accents("café") == "cafe"
        assert strip_accents("Árbol") == "Arbol"
        assert strip_accents("pingüino") == "pinguino"
        assert strip_accents("señor") == "senor"

    def test_sin_acentos(self) -> None:
        assert strip_accents("casa") == "casa"

    def test_vacia(self) -> None:
        assert strip_accents("") == ""

    def test_solo_acentos(self) -> None:
        # Combinaciones unicode huérfanas
        assert strip_accents("\u0301") == ""

    def test_mayusculas(self) -> None:
        # strip_accents no cambia el caso
        assert strip_accents("CAFÉ") == "CAFE"

    def test_caracteres_no_latinos(self) -> None:
        assert strip_accents("日本語") == "日本語"


class TestNormalizeKey:
    def test_basico(self) -> None:
        assert normalize_key("Café") == "cafe"
        assert normalize_key("CAFÉ") == "cafe"

    def test_sin_acentos(self) -> None:
        assert normalize_key("casa") == "casa"

    def test_remove_accents_false(self) -> None:
        assert normalize_key("Café", remove_accents=False) == "café"

    def test_vacia(self) -> None:
        assert normalize_key("") == ""

    def test_espacios_no_se_tocan(self) -> None:
        # normalize_key no hace strip, solo lower + sin acentos
        assert normalize_key("  Casa  ") == "  casa  "
