"""Tests de la capa de persistencia (SQLAlchemy)."""

from __future__ import annotations

from pathlib import Path

import pytest

from autocomplete import Storage


class TestCRUD:
    def test_add_y_all_words(self, tmp_sqlite_mem: Storage) -> None:
        tmp_sqlite_mem.add_word("casa", weight=3, source="test")
        tmp_sqlite_mem.add_word("casco", weight=1, source="test")

        palabras = dict(tmp_sqlite_mem.all_words())
        assert palabras == {"casa": 3, "casco": 1}

    def test_add_word_incrementa_peso(self, tmp_sqlite_mem: Storage) -> None:
        tmp_sqlite_mem.add_word("casa", weight=2)
        tmp_sqlite_mem.add_word("casa", weight=5)
        assert dict(tmp_sqlite_mem.all_words()) == {"casa": 7}

    def test_add_many(self, tmp_sqlite_mem: Storage) -> None:
        n = tmp_sqlite_mem.add_many([("a", 1), ("b", 2), ("c", 3)])
        assert n == 3
        assert tmp_sqlite_mem.word_count() == 3

    def test_remove_word(self, tmp_sqlite_mem: Storage) -> None:
        tmp_sqlite_mem.add_word("casa")
        assert tmp_sqlite_mem.remove_word("casa") is True
        assert tmp_sqlite_mem.remove_word("casa") is False

    def test_word_count(self, tmp_sqlite_mem: Storage) -> None:
        assert tmp_sqlite_mem.word_count() == 0
        tmp_sqlite_mem.add_word("a")
        tmp_sqlite_mem.add_word("b")
        assert tmp_sqlite_mem.word_count() == 2


class TestHistorial:
    def test_add_y_recent(self, tmp_sqlite_mem: Storage) -> None:
        tmp_sqlite_mem.add_history(
            command="gti status",
            corrected="git status",
            executed=True,
            exit_code=0,
        )
        rows = tmp_sqlite_mem.recent_history(limit=10)
        assert len(rows) == 1
        assert rows[0].command == "gti status"
        assert rows[0].corrected == "git status"
        assert rows[0].executed is True
        assert rows[0].exit_code == 0

    def test_clear_history(self, tmp_sqlite_mem: Storage) -> None:
        tmp_sqlite_mem.add_history(command="x")
        tmp_sqlite_mem.add_history(command="y")
        n = tmp_sqlite_mem.clear_history()
        assert n == 2
        assert tmp_sqlite_mem.recent_history() == []


class TestPreferencias:
    def test_set_y_get(self, tmp_sqlite_mem: Storage) -> None:
        tmp_sqlite_mem.set_pref("tema", "oscuro")
        assert tmp_sqlite_mem.get_pref("tema") == "oscuro"

    def test_get_default(self, tmp_sqlite_mem: Storage) -> None:
        assert tmp_sqlite_mem.get_pref("no-existe", "fallback") == "fallback"

    def test_valor_json(self, tmp_sqlite_mem: Storage) -> None:
        tmp_sqlite_mem.set_pref("lista", [1, 2, 3])
        assert tmp_sqlite_mem.get_pref("lista") == [1, 2, 3]

    def test_all_prefs(self, tmp_sqlite_mem: Storage) -> None:
        tmp_sqlite_mem.set_pref("a", 1)
        tmp_sqlite_mem.set_pref("b", "dos")
        assert tmp_sqlite_mem.all_prefs() == {"a": 1, "b": "dos"}


class TestMantenimiento:
    def test_reset(self, tmp_sqlite_mem: Storage) -> None:
        tmp_sqlite_mem.add_word("x")
        tmp_sqlite_mem.add_history(command="y")
        tmp_sqlite_mem.set_pref("z", 1)

        tmp_sqlite_mem.reset()

        assert tmp_sqlite_mem.word_count() == 0
        assert tmp_sqlite_mem.recent_history() == []
        assert tmp_sqlite_mem.all_prefs() == {}

    def test_backup_y_restore_sqlite(self, tmp_sqlite: Storage, tmp_path: Path) -> None:
        tmp_sqlite.add_word("casa", weight=5)
        tmp_sqlite.add_word("casco", weight=3)

        backup = tmp_sqlite.backup(str(tmp_path / "respaldo.db"))
        assert backup.exists()

        tmp_sqlite.reset()
        assert tmp_sqlite.word_count() == 0

        tmp_sqlite.restore(str(backup))
        assert tmp_sqlite.word_count() == 2

    def test_vacuum_sqlite(self, tmp_sqlite_mem: Storage) -> None:
        tmp_sqlite_mem.add_word("x")
        tmp_sqlite_mem.vacuum()  # no debe lanzar

    def test_dialect_y_flags(self, tmp_sqlite_mem: Storage) -> None:
        assert tmp_sqlite_mem.dialect == "sqlite"
        assert tmp_sqlite_mem.is_sqlite is True
        assert tmp_sqlite_mem.is_postgres is False
        assert tmp_sqlite_mem.is_mysql is False

    def test_db_size_bytes_sqlite(self, tmp_sqlite: Storage) -> None:
        tmp_sqlite.add_word("x")
        size = tmp_sqlite.db_size_bytes()
        assert size is not None
        assert size > 0

    def test_backup_output_custom(self, tmp_sqlite: Storage, tmp_path: Path) -> None:
        target = tmp_path / "custom.db"
        result = tmp_sqlite.backup(str(target))
        assert result == target.resolve()
        assert target.exists()
