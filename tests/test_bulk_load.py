"""Tests de carga masiva: `bulk_load` y `bulk_load_dir`."""

from __future__ import annotations

import gzip
from pathlib import Path

from autocomplete import Autocomplete


class TestBulkLoad:
    def test_txt(self, tmp_path: Path) -> None:
        f = tmp_path / "palabras.txt"
        f.write_text("casa\ncasamiento\n\n# comentario\ncasco\n", encoding="utf-8")

        ac = Autocomplete()
        stats = ac.bulk_load(f)
        assert stats.loaded == 3
        assert stats.skipped == 2
        assert stats.total == 5
        assert ac.suggestions("cas") == [
            "casa",
            "casamiento",
            "casco",
        ]

    def test_tsv_con_pesos(self, tmp_path: Path) -> None:
        f = tmp_path / "palabras.tsv"
        f.write_text("casa\t1\ncasamiento\t10\ncasco\t5\n", encoding="utf-8")

        ac = Autocomplete()
        stats = ac.bulk_load(f, separator="\t")
        assert stats.loaded == 3
        assert ac.suggestions("cas") == [
            "casamiento",
            "casco",
            "casa",
        ]

    def test_gz(self, tmp_path: Path) -> None:
        f = tmp_path / "palabras.txt.gz"
        with gzip.open(f, "wt", encoding="utf-8") as gz:
            gz.write("casa\ncasco\nperro\n")

        ac = Autocomplete.from_file(f)
        assert ac.suggestions("cas") == ["casa", "casco"]

    def test_errores(self, tmp_path: Path) -> None:
        f = tmp_path / "palabras.tsv"
        f.write_text("casa\t1\ncasco\tno-es-numero\n", encoding="utf-8")

        ac = Autocomplete()
        stats = ac.bulk_load(f, separator="\t")
        assert stats.loaded == 1
        assert stats.skipped == 1
        assert len(stats.errors) == 1

    def test_progreso(self, tmp_path: Path) -> None:
        f = tmp_path / "palabras.txt"
        f.write_text(
            "\n".join(f"p{i}" for i in range(250)) + "\n",
            encoding="utf-8",
        )

        calls: list[int] = []
        ac = Autocomplete()
        ac.bulk_load(f, on_progress=calls.append, progress_every=100)
        assert calls == [100, 200]

    def test_comentarios_desactivados(self, tmp_path: Path) -> None:
        f = tmp_path / "palabras.txt"
        f.write_text("#no-es-comentario\ncasa\n", encoding="utf-8")

        ac = Autocomplete()
        stats = ac.bulk_load(f, comment_prefix=None)
        assert stats.loaded == 2


class TestBulkLoadDir:
    def test_directorio_simple(self, tmp_path: Path) -> None:
        d = tmp_path / "comandos"
        d.mkdir()
        (d / "01-git.txt").write_text("git\ngit-push\n", encoding="utf-8")
        (d / "02-docker.txt").write_text("docker\ndocker-run\n", encoding="utf-8")

        ac = Autocomplete()
        stats = ac.bulk_load_dir(d)
        assert stats.total_files == 2
        assert stats.loaded == 4
        assert "git" in ac.suggestions("gi")
        assert "docker" in ac.suggestions("do")

    def test_recursivo(self, tmp_path: Path) -> None:
        d = tmp_path / "comandos"
        (d / "sub").mkdir(parents=True)
        (d / "01-a.txt").write_text("a\n", encoding="utf-8")
        (d / "sub" / "02-b.txt").write_text("b\n", encoding="utf-8")

        ac = Autocomplete()
        stats = ac.bulk_load_dir(d, recursive=True)
        assert stats.total_files == 2
        assert stats.loaded == 2

    def test_sin_recursivo_no_baja(self, tmp_path: Path) -> None:
        d = tmp_path / "comandos"
        (d / "sub").mkdir(parents=True)
        (d / "01-a.txt").write_text("a\n", encoding="utf-8")
        (d / "sub" / "02-b.txt").write_text("b\n", encoding="utf-8")

        ac = Autocomplete()
        stats = ac.bulk_load_dir(d, recursive=False)
        assert stats.total_files == 1
        assert stats.loaded == 1

    def test_directorio_inexistente(self, tmp_path: Path) -> None:
        ac = Autocomplete()
        try:
            ac.bulk_load_dir(tmp_path / "no-existe")
        except FileNotFoundError:
            return
        raise AssertionError("Se esperaba FileNotFoundError")

    def test_pattern_personalizado(self, tmp_path: Path) -> None:
        d = tmp_path / "comandos"
        d.mkdir()
        (d / "a.txt").write_text("a\n", encoding="utf-8")
        (d / "b.tsv").write_text("b\t5\n", encoding="utf-8")

        ac = Autocomplete()
        stats = ac.bulk_load_dir(d, pattern="*.tsv", separator="\t")
        assert stats.total_files == 1
        assert stats.loaded == 1
