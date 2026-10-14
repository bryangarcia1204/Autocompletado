import gzip
from pathlib import Path

import pytest

from autocomplete import Autocomplete, InvalidWordError, strip_accents


# ---------------------------------------------------------------------- #
# Fixtures
# ---------------------------------------------------------------------- #
@pytest.fixture
def ac() -> Autocomplete:
    return Autocomplete(["casa", "casamiento", "casco", "perro", "pez"])


# ---------------------------------------------------------------------- #
# Tests básicos
# ---------------------------------------------------------------------- #
def test_sugerencias_basicas(ac):
    assert ac.suggestions("cas") == ["casa", "casamiento", "casco"]


def test_sin_coincidencias(ac):
    assert ac.suggestions("zzz") == []


def test_prefijo_vacio(ac):
    assert ac.suggestions("") == []


def test_limit(ac):
    assert ac.suggestions("cas", limit=2) == ["casa", "casamiento"]


def test_orden_por_frecuencia():
    ac = Autocomplete()
    ac.add_word("casa", weight=1)
    ac.add_word("casamiento", weight=10)
    ac.add_word("casco", weight=5)
    assert ac.suggestions("cas") == ["casamiento", "casco", "casa"]


def test_orden_alfabetico():
    ac = Autocomplete()
    ac.add_word("casa", weight=1)
    ac.add_word("casamiento", weight=10)
    assert ac.suggestions("cas", sort_by_frequency=False) == [
        "casa",
        "casamiento",
    ]


def test_preserva_mayusculas():
    ac = Autocomplete(["Casa", "casamiento"])
    assert "Casa" in ac.suggestions("cas")


def test_add_word_invalida():
    ac = Autocomplete()
    with pytest.raises(InvalidWordError):
        ac.add_word("")
    with pytest.raises(InvalidWordError):
        ac.add_word("   ")
    with pytest.raises(InvalidWordError):
        ac.add_word("x", weight=0)


def test_add_dict():
    ac = Autocomplete()
    ac.add_words({"casa": 3, "casco": 1})
    assert ac.suggestions("cas") == ["casa", "casco"]


def test_len(ac):
    assert len(ac) == 5


# ---------------------------------------------------------------------- #
# Acentos
# ---------------------------------------------------------------------- #
def test_strip_accents():
    assert strip_accents("café") == "cafe"
    assert strip_accents("Árbol") == "Arbol"
    assert strip_accents("pingüino") == "pinguino"
    assert strip_accents("señor") == "senor"
    assert strip_accents("") == ""


def test_busqueda_sin_acentos():
    ac = Autocomplete(["café", "cafetería", "cama"])
    assert ac.suggestions("cafe") == ["café", "cafetería"]
    assert ac.suggestions("café") == ["café", "cafetería"]


def test_desactivar_normalizacion():
    ac = Autocomplete(["café"], remove_accents=False)
    assert ac.suggestions("cafe") == []
    assert ac.suggestions("café") == ["café"]


# ---------------------------------------------------------------------- #
# bulk_load
# ---------------------------------------------------------------------- #
def test_bulk_load_txt(tmp_path: Path):
    f = tmp_path / "palabras.txt"
    f.write_text("casa\ncasamiento\n\n# comentario\ncasco\n", encoding="utf-8")

    ac = Autocomplete()
    stats = ac.bulk_load(f)
    assert stats.loaded == 3
    assert stats.skipped == 2
    assert stats.total == 5
    assert ac.suggestions("cas") == ["casa", "casamiento", "casco"]


def test_bulk_load_tsv(tmp_path: Path):
    f = tmp_path / "palabras.tsv"
    f.write_text("casa\t1\ncasamiento\t10\ncasco\t5\n", encoding="utf-8")

    ac = Autocomplete()
    stats = ac.bulk_load(f, separator="\t")
    assert stats.loaded == 3
    assert ac.suggestions("cas") == ["casamiento", "casco", "casa"]


def test_bulk_load_gz(tmp_path: Path):
    f = tmp_path / "palabras.txt.gz"
    with gzip.open(f, "wt", encoding="utf-8") as gz:
        gz.write("casa\ncasco\nperro\n")

    ac = Autocomplete.from_file(f)
    assert ac.suggestions("cas") == ["casa", "casco"]


def test_bulk_load_errores(tmp_path: Path):
    f = tmp_path / "palabras.tsv"
    f.write_text("casa\t1\ncasco\tno-es-numero\n", encoding="utf-8")

    ac = Autocomplete()
    stats = ac.bulk_load(f, separator="\t")
    assert stats.loaded == 1
    assert stats.skipped == 1
    assert len(stats.errors) == 1


def test_bulk_load_progreso(tmp_path: Path):
    f = tmp_path / "palabras.txt"
    f.write_text("\n".join(f"p{i}" for i in range(250)) + "\n", encoding="utf-8")

    calls = []
    ac = Autocomplete()
    ac.bulk_load(f, on_progress=calls.append, progress_every=100)
    assert calls == [100, 200]