"""Tests de la CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autocomplete.interfaces.cli import build_parser, main


# ---------------------------------------------------------------------- #
# Fixtures
# ---------------------------------------------------------------------- #
@pytest.fixture
def cli_env(tmp_path: Path, monkeypatch):
    """Aísla la config y la BD en un directorio temporal."""
    cfg = tmp_path / "config.json"
    db = tmp_path / "data.db"
    monkeypatch.setenv("AUTOCOMPLETE_CONFIG", str(cfg))
    return {"config": cfg, "db": db}


@pytest.fixture
def db_url(cli_env, tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'data.db'}"


# ---------------------------------------------------------------------- #
# Parser
# ---------------------------------------------------------------------- #
class TestParser:
    def test_build_parser(self) -> None:
        p = build_parser()
        assert p is not None

    def test_subcomandos_disponibles(self) -> None:
        p = build_parser()
        # Ejecutar --help debe funcionar sin explotar
        with pytest.raises(SystemExit):
            p.parse_args(["--help"])

    def test_comando_desconocido(self) -> None:
        p = build_parser()
        with pytest.raises(SystemExit):
            p.parse_args(["xyz"])

    def test_sin_subcomando(self) -> None:
        p = build_parser()
        with pytest.raises(SystemExit):
            p.parse_args([])


# ---------------------------------------------------------------------- #
# config
# ---------------------------------------------------------------------- #
class TestConfig:
    def test_show(self, cli_env, capsys) -> None:
        rc = main(["config", "show"])
        out = capsys.readouterr().out
        assert rc == 0
        data = json.loads(out)
        assert "max_distance" in data

    def test_path(self, cli_env, capsys) -> None:
        rc = main(["config", "path"])
        out = capsys.readouterr().out
        assert rc == 0
        assert str(cli_env["config"]) in out

    def test_set_y_persiste(self, cli_env, capsys) -> None:
        rc = main(["config", "set", "max_distance", "5"])
        assert rc == 0
        cfg = json.loads(cli_env["config"].read_text(encoding="utf-8"))
        assert cfg["max_distance"] == 5

    def test_set_valor_string(self, cli_env) -> None:
        rc = main(["config", "set", "database_url", "sqlite:///:memory:"])
        assert rc == 0
        cfg = json.loads(cli_env["config"].read_text(encoding="utf-8"))
        assert cfg["database_url"] == "sqlite:///:memory:"

    def test_reset(self, cli_env) -> None:
        main(["config", "set", "max_distance", "99"])
        rc = main(["config", "reset"])
        assert rc == 0
        cfg = json.loads(cli_env["config"].read_text(encoding="utf-8"))
        assert cfg["max_distance"] == 2


# ---------------------------------------------------------------------- #
# db
# ---------------------------------------------------------------------- #
class TestDb:
    def test_init(self, db_url, capsys) -> None:
        rc = main(["--db-url", db_url, "db", "init"])
        assert rc == 0
        assert "BD lista" in capsys.readouterr().out

    def test_info(self, db_url, capsys) -> None:
        rc = main(["--db-url", db_url, "db", "info"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "SQLite" in out or "sqlite" in out

    def test_add_y_list(self, db_url, capsys) -> None:
        rc = main(["--db-url", db_url, "db", "add", "casa", "casco"])
        assert rc == 0
        capsys.readouterr()

        rc = main(["--db-url", db_url, "db", "list"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "casa" in out and "casco" in out

    def test_add_con_peso(self, db_url, capsys) -> None:
        rc = main(
            ["--db-url", db_url, "db", "add", "casa", "--weight", "5"]
        )
        assert rc == 0

    def test_remove(self, db_url, capsys) -> None:
        main(["--db-url", db_url, "db", "add", "casa"])
        capsys.readouterr()
        rc = main(["--db-url", db_url, "db", "remove", "casa"])
        assert rc == 0
        assert "Eliminadas 1" in capsys.readouterr().out

    def test_history_vacio(self, db_url, capsys) -> None:
        rc = main(["--db-url", db_url, "db", "history"])
        assert rc == 0

    def test_history_clear(self, db_url, capsys) -> None:
        rc = main(["--db-url", db_url, "db", "history", "--clear"])
        assert rc == 0

    def test_restart_con_yes(self, db_url, capsys) -> None:
        main(["--db-url", db_url, "db", "add", "casa"])
        capsys.readouterr()
        rc = main(["--db-url", db_url, "db", "restart", "--yes"])
        assert rc == 0
        assert "reiniciada" in capsys.readouterr().out

    def test_restart_cancelado(self, db_url, monkeypatch, capsys) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "n")
        rc = main(["--db-url", db_url, "db", "restart"])
        assert rc == 1
        assert "Cancelado" in capsys.readouterr().out

    def test_backup_y_restore(self, db_url, tmp_path, capsys) -> None:
        main(["--db-url", db_url, "db", "add", "casa"])
        capsys.readouterr()

        backup = tmp_path / "respaldo.db"
        rc = main(["--db-url", db_url, "db", "backup", "-o", str(backup)])
        assert rc == 0
        assert backup.exists()

        # Restaurar sin preguntar
        rc = main(["--db-url", db_url, "db", "restore", str(backup), "--yes"])
        assert rc == 0

    def test_restore_archivo_inexistente(self, db_url, tmp_path, capsys) -> None:
        rc = main(
            ["--db-url", db_url, "db", "restore", str(tmp_path / "no.db"), "--yes"]
        )
        assert rc == 2

    def test_vacuum(self, db_url, capsys) -> None:
        rc = main(["--db-url", db_url, "db", "vacuum"])
        assert rc == 0

    def test_db_sin_storage(self, capsys) -> None:
        rc = main(["--no-db", "db", "init"])
        assert rc == 2
        assert "no disponible" in capsys.readouterr().err


# ---------------------------------------------------------------------- #
# suggest / correct
# ---------------------------------------------------------------------- #
class TestSuggestCorrect:
    def test_suggest_sin_palabras(self, db_url, capsys) -> None:
        rc = main(["--no-daemon", "--db-url", db_url, "suggest", "cas"])
        assert rc == 1

    def test_suggest_con_palabras(self, db_url, capsys) -> None:
        main(["--no-daemon", "--db-url", db_url, "db", "add", "casa", "casco"])
        capsys.readouterr()

        rc = main(["--no-daemon", "--db-url", db_url, "suggest", "cas"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "casa" in out
        assert "casco" in out

    def test_suggest_limit(self, db_url, capsys) -> None:
        main([
            "--no-daemon", "--db-url", db_url,
            "db", "add", "casa", "casco", "casamiento",
        ])
        capsys.readouterr()
        rc = main([
            "--no-daemon", "--db-url", db_url,
            "suggest", "cas", "--limit", "1",
        ])
        out = capsys.readouterr().out
        assert rc == 0
        assert out.count("\n") == 1

    def test_correct_sin_resultados(self, db_url, capsys) -> None:
        rc = main(["--no-daemon", "--db-url", db_url, "correct", "xyzxyz"])
        assert rc == 1

    def test_correct_con_resultados(self, db_url, capsys) -> None:
        main(["--no-daemon", "--db-url", db_url, "db", "add", "casa"])
        capsys.readouterr()
        rc = main(["--no-daemon", "--db-url", db_url, "correct", "casaa"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "casa" in out

    def test_correct_execute_dry(self, db_url, capsys, monkeypatch) -> None:
        main(["--no-daemon", "--db-url", db_url, "db", "add", "python"])
        capsys.readouterr()
        monkeypatch.setattr("builtins.input", lambda _: "n")
        rc = main([
            "--no-daemon", "--db-url", db_url,
            "correct", "pyton", "--execute",
        ])
        assert rc in (0, 1)


# ---------------------------------------------------------------------- #
# repl / shell (interactivos → input mock)
# ---------------------------------------------------------------------- #
class TestInteractivos:
    def test_repl_salir(self, db_url, monkeypatch, capsys) -> None:
        main(["--no-daemon", "--db-url", db_url, "db", "add", "casa", "casco"])
        capsys.readouterr()

        inputs = iter(["cas", "salir"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        rc = main(["--no-daemon", "--db-url", db_url, "repl"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "casa" in out

    def test_repl_linea_vacia(self, db_url, monkeypatch, capsys) -> None:
        inputs = iter(["", "salir"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        rc = main(["--no-daemon", "--db-url", db_url, "repl"])
        assert rc == 0

    def test_shell_dry_run(self, db_url, monkeypatch, capsys) -> None:
        main(["--no-daemon", "--db-url", db_url, "db", "add", "python"])
        capsys.readouterr()
        inputs = iter(["pyton -V", "salir"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        rc = main(["--no-daemon", "--db-url", db_url, "shell", "--dry-run"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "dry-run" in out or "Corrección" in out

    def test_shell_comando_conocido(self, db_url, monkeypatch, capsys) -> None:
        main(["--no-daemon", "--db-url", db_url, "db", "add", "python"])
        capsys.readouterr()
        inputs = iter(["python -c pass", "salir"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        rc = main(["--no-daemon", "--db-url", db_url, "shell", "--dry-run"])
        assert rc == 0


# ---------------------------------------------------------------------- #
# load-dir
# ---------------------------------------------------------------------- #
class TestLoadDir:
    def test_load_dir(self, db_url, tmp_path, capsys) -> None:
        d = tmp_path / "cmds"
        d.mkdir()
        (d / "a.txt").write_text("casa\ncasco\n", encoding="utf-8")
        (d / "b.txt").write_text("perro\n", encoding="utf-8")

        rc = main(["--db-url", db_url, "load-dir", str(d)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "3 palabras" in out

    def test_load_dir_replace(self, db_url, tmp_path, capsys) -> None:
        d = tmp_path / "cmds"
        d.mkdir()
        (d / "a.txt").write_text("nuevo\n", encoding="utf-8")

        main(["--db-url", db_url, "db", "add", "viejo"])
        capsys.readouterr()

        rc = main(["--db-url", db_url, "load-dir", str(d), "--replace"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "vaciada" in out

    def test_load_dir_inexistente(self, db_url, tmp_path, capsys) -> None:
        rc = main(
            ["--db-url", db_url, "load-dir", str(tmp_path / "nada")]
        )
        assert rc == 2

    def test_load_dir_sin_storage(self, tmp_path, capsys) -> None:
        rc = main(["--no-db", "load-dir", str(tmp_path)])
        assert rc == 2


# ---------------------------------------------------------------------- #
# daemon
# ---------------------------------------------------------------------- #
class TestDaemonCli:
    def test_status(self, tmp_path, monkeypatch, capsys) -> None:
        from autocomplete.server import daemon as dm

        monkeypatch.setattr(dm, "PORT_FILE", tmp_path / "nada.port")
        monkeypatch.setattr(dm, "PID_FILE", tmp_path / "nada.pid")
        rc = main(["daemon", "status"])
        assert rc == 1

    def test_reload_sin_daemon(self, tmp_path, monkeypatch, capsys) -> None:
        from autocomplete.server import daemon as dm

        monkeypatch.setattr(dm, "PORT_FILE", tmp_path / "nada.port")
        rc = main(["daemon", "reload"])
        assert rc == 1


# ---------------------------------------------------------------------- #
# install-ps
# ---------------------------------------------------------------------- #
class TestInstallPs:
    def test_install_ps(self, cli_env, capsys) -> None:
        rc = main(["install-ps"])
        out = capsys.readouterr().out
        # Puede ser 0 si el asset existe, o 1 si no
        assert rc in (0, 1)
        if rc == 0:
            assert "Wrapper instalado" in out