"""Tests de las estadísticas de carga."""

from __future__ import annotations

from autocomplete.core.stats import LoadDirStats, LoadStats


class TestLoadStats:
    def test_defaults(self) -> None:
        s = LoadStats()
        assert s.loaded == 0
        assert s.skipped == 0
        assert s.errors == []
        assert s.total == 0

    def test_total(self) -> None:
        s = LoadStats(loaded=5, skipped=2)
        assert s.total == 7

    def test_str(self) -> None:
        s = LoadStats(loaded=3, skipped=1, errors=["e1", "e2"])
        text = str(s)
        assert "loaded=3" in text
        assert "skipped=1" in text
        assert "errors=2" in text


class TestLoadDirStats:
    def test_vacio(self) -> None:
        s = LoadDirStats()
        assert s.total_files == 0
        assert s.loaded == 0
        assert s.skipped == 0
        assert s.errors == []

    def test_con_archivos(self) -> None:
        s = LoadDirStats(
            files={
                "a.txt": LoadStats(loaded=3, skipped=1),
                "b.txt": LoadStats(loaded=5, skipped=2, errors=["x"]),
            }
        )
        assert s.total_files == 2
        assert s.loaded == 8
        assert s.skipped == 3
        assert len(s.errors) == 1
        assert s.errors[0].startswith("[b.txt]")

    def test_str(self) -> None:
        s = LoadDirStats(files={"a.txt": LoadStats(loaded=1)})
        text = str(s)
        assert "files=1" in text