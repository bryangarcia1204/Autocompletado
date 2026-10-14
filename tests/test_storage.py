"""Tests de la capa de persistencia (SQLAlchemy)."""

from __future__ import annotations

from pathlib import Path

import pytest

from autocomplete import Storage

from unittest.mock import MagicMock

from autocomplete.storage import repository as repo_mod

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


class TestBackupOtrosMotores:
    def test_backup_postgres_mocked(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        storage = repo_mod.Storage("sqlite:///:memory:")
        storage.url = "postgresql+psycopg://u:p@localhost:5432/db"

        monkeypatch.setattr(
            repo_mod.Storage, "is_sqlite", property(lambda self: False)
        )
        monkeypatch.setattr(
            repo_mod.Storage, "is_postgres", property(lambda self: True)
        )
        monkeypatch.setattr(
            repo_mod.Storage, "is_mysql", property(lambda self: False)
        )
        # Forzar que shutil.which() no encuentre nada y use el fallback
        monkeypatch.setenv("AUTOCOMPLETE_PG_DUMP", "/falso/pg_dump")

        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return MagicMock(returncode=0)

        monkeypatch.setattr(repo_mod.subprocess, "run", fake_run)

        target = tmp_path / "backup.sql"
        storage.backup(str(target))

        assert calls, "subprocess.run no fue llamado"
        cmd = calls[0]
        assert isinstance(cmd, list), f"cmd debe ser list, es {type(cmd)}"
        assert Path(cmd[0]).name.lower() in ("pg_dump", "pg_dump.exe")

    def test_backup_mysql_mocked(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        storage = repo_mod.Storage("sqlite:///:memory:")
        storage.url = "mysql+pymysql://u:p@localhost/db"

        monkeypatch.setattr(
            repo_mod.Storage, "is_sqlite", property(lambda self: False)
        )
        monkeypatch.setattr(
            repo_mod.Storage, "is_postgres", property(lambda self: False)
        )
        monkeypatch.setattr(
            repo_mod.Storage, "is_mysql", property(lambda self: True)
        )
        monkeypatch.setenv("AUTOCOMPLETE_MYSQLDUMP", "/falso/mysqldump")

        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return MagicMock(returncode=0)

        monkeypatch.setattr(repo_mod.subprocess, "run", fake_run)

        storage.backup(str(tmp_path / "b.sql"))

        assert calls
        assert isinstance(calls[0], list)
        assert Path(calls[0][0]).name.lower() in (
            "mysqldump",
            "mysqldump.exe",
        )

    def test_backup_motor_desconocido(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        storage = repo_mod.Storage("sqlite:///:memory:")
        storage.url = "oracle://x/y"

        monkeypatch.setattr(
            repo_mod.Storage, "is_sqlite", property(lambda self: False)
        )
        monkeypatch.setattr(
            repo_mod.Storage, "is_postgres", property(lambda self: False)
        )
        monkeypatch.setattr(
            repo_mod.Storage, "is_mysql", property(lambda self: False)
        )

        with pytest.raises(NotImplementedError):
            storage.backup(str(tmp_path / "x.sql"))

    def test_backup_sin_destino_usa_base_dir(
        self, tmp_sqlite, tmp_path
    ) -> None:
        result = tmp_sqlite.backup(base_dir=tmp_path)
        assert result.parent == tmp_path / "backups"
        assert result.exists()
        assert result.name.startswith("backup-")
        assert result.suffix == ".db"

    def test_backup_output_no_crea_base_dir(
        self, tmp_sqlite, tmp_path
    ) -> None:
        """Si se da `output`, no debe crear <base_dir>/backups/."""
        custom = tmp_path / "explicito.db"
        otro = tmp_path / "otro"

        result = tmp_sqlite.backup(str(custom), base_dir=otro)

        assert result == custom.resolve()
        assert custom.exists()
        assert not otro.exists(), (
            f"No debería existir {otro} cuando se da `output`"
        )

    def test_backup_usa_config_dir_por_defecto(
        self, tmp_sqlite, monkeypatch, tmp_path
    ) -> None:
        import autocomplete.config.settings as settings_mod

        monkeypatch.setattr(
            settings_mod, "config_dir", lambda: tmp_path
        )

        result = tmp_sqlite.backup()
        assert result.parent == tmp_path / "backups"

    def test_backup_sqlite_archivo_inexistente(
        self, tmp_path
    ) -> None:
        db_path = tmp_path / "no.db"
        storage = repo_mod.Storage(f"sqlite:///{db_path}")
        storage.close()
        db_path.unlink(missing_ok=True)

        with pytest.raises(FileNotFoundError):
            storage.backup(str(tmp_path / "out.db"))


class TestRestoreOtrosMotores:
    def test_restore_archivo_inexistente(self, tmp_sqlite, tmp_path) -> None:
        with pytest.raises(FileNotFoundError):
            tmp_sqlite.restore(str(tmp_path / "no-existe.db"))

    def test_restore_motor_desconocido(
        self, tmp_path, monkeypatch
    ) -> None:
        storage = repo_mod.Storage("sqlite:///:memory:")
        storage.url = "oracle://x/y"

        monkeypatch.setattr(
            repo_mod.Storage, "is_sqlite", property(lambda self: False)
        )
        monkeypatch.setattr(
            repo_mod.Storage, "is_postgres", property(lambda self: False)
        )
        monkeypatch.setattr(
            repo_mod.Storage, "is_mysql", property(lambda self: False)
        )

        backup = tmp_path / "b.sql"
        backup.write_text("-- sql")
        with pytest.raises(NotImplementedError):
            storage.restore(str(backup))


class TestVacuumOtrosMotores:
    def test_vacuum_motor_desconocido(self, monkeypatch) -> None:
        storage = repo_mod.Storage("sqlite:///:memory:")
        storage.url = "oracle://x/y"

        monkeypatch.setattr(
            repo_mod.Storage, "is_sqlite", property(lambda self: False)
        )
        monkeypatch.setattr(
            repo_mod.Storage, "is_postgres", property(lambda self: False)
        )
        monkeypatch.setattr(
            repo_mod.Storage, "is_mysql", property(lambda self: False)
        )

        with pytest.raises(NotImplementedError):
            storage.vacuum()


class TestCicloVida:
    def test_close(self, tmp_sqlite_mem) -> None:
        tmp_sqlite_mem.close()

    def test_context_manager(self, tmp_path) -> None:
        with repo_mod.Storage(
            f"sqlite:///{tmp_path / 'ctx.db'}"
        ) as s:
            s.add_word("x")
            assert s.word_count() == 1
