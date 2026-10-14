"""Tests del daemon TCP y su cliente."""

from __future__ import annotations

import socket
import threading
import time
from pathlib import Path

import pytest

from autocomplete import Autocomplete
from autocomplete.server import daemon as dm
from autocomplete.server.client import DaemonClient, is_available


# ---------------------------------------------------------------------- #
# Fixtures
# ---------------------------------------------------------------------- #
@pytest.fixture
def daemon_server(tmp_path: Path, monkeypatch):
    """Arranca un DaemonServer en un puerto libre y lo apaga al final."""
    # Aislar archivos de estado
    port_file = tmp_path / "daemon.port"
    pid_file = tmp_path / "daemon.pid"
    monkeypatch.setattr(dm, "PORT_FILE", port_file)
    monkeypatch.setattr(dm, "PID_FILE", pid_file)

    server = dm.DaemonServer(("127.0.0.1", 0), dm._Handler)
    port = server.server_address[1]

    # Cargar palabras de prueba sin pasar por la BD real
    ac = Autocomplete(["casa", "casamiento", "casco", "perro"])
    server.ac = ac
    server.storage = None

    # Publicar puerto/pid
    port_file.write_text(str(port))
    pid_file.write_text("0")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Pequeña espera para que el socket esté listo
    time.sleep(0.05)

    yield server

    server.shutdown()
    server.server_close()
    thread.join(timeout=2)
    for f in (port_file, pid_file):
        try:
            f.unlink()
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------- #
# Protocolo directo (dispatch)
# ---------------------------------------------------------------------- #
class TestDispatch:
    def test_ping(self, daemon_server) -> None:
        r = daemon_server.dispatch({"op": "ping"})
        assert r["ok"] is True
        assert r["pong"] is True

    def test_suggest(self, daemon_server) -> None:
        r = daemon_server.dispatch(
            {"op": "suggest", "prefix": "cas", "limit": 2}
        )
        assert r["ok"] is True
        assert len(r["suggestions"]) == 2

    def test_correct(self, daemon_server) -> None:
        r = daemon_server.dispatch(
            {"op": "correct", "word": "casaa", "max_distance": 1}
        )
        assert r["ok"] is True
        assert any(w == "casa" for w, _ in r["corrections"])

    def test_contains(self, daemon_server) -> None:
        r = daemon_server.dispatch({"op": "contains", "word": "casa"})
        assert r["ok"] is True
        assert r["contains"] is True

    def test_stats(self, daemon_server) -> None:
        r = daemon_server.dispatch({"op": "stats"})
        assert r["ok"] is True
        assert r["words"] == 4

    def test_unknown_op(self, daemon_server) -> None:
        r = daemon_server.dispatch({"op": "noexiste"})
        assert r["ok"] is False
        assert "unknown op" in r["error"]

    def test_not_loaded(self) -> None:
        server = dm.DaemonServer(("127.0.0.1", 0), dm._Handler)
        try:
            r = server.dispatch({"op": "suggest", "prefix": "x"})
            assert r["ok"] is False
            assert "not loaded" in r["error"]
        finally:
            server.server_close()

    def test_reload(self, daemon_server) -> None:
        r = daemon_server.dispatch({"op": "reload"})
        assert r["ok"] is True
        assert r["reloaded"] is True

    def test_shutdown_op(self, daemon_server) -> None:
        r = daemon_server.dispatch({"op": "shutdown"})
        assert r["ok"] is True

    def test_excepcion_interna(self, daemon_server) -> None:
        # Forzar un error: prefix no es string hace que suggestions() falle
        r = daemon_server.dispatch({"op": "suggest", "prefix": 123})
        assert r["ok"] is False


# ---------------------------------------------------------------------- #
# Cliente TCP end-to-end
# ---------------------------------------------------------------------- #
class TestClient:
    def test_ping(self, daemon_server) -> None:
        assert DaemonClient().ping() is True

    def test_suggest(self, daemon_server) -> None:
        r = DaemonClient().suggest("cas", limit=5)
        assert r is not None
        assert "casa" in r

    def test_correct(self, daemon_server) -> None:
        r = DaemonClient().correct("casaa", max_distance=1)
        assert r is not None
        assert any(w == "casa" for w, _ in r)

    def test_contains(self, daemon_server) -> None:
        assert DaemonClient().contains("casa") is True
        assert DaemonClient().contains("xyz") is False

    def test_reload(self, daemon_server) -> None:
        assert DaemonClient().reload() is True

    def test_is_available(self, daemon_server) -> None:
        assert is_available() is True

    def test_sin_daemon(self, tmp_path, monkeypatch) -> None:
        # Sin archivo de puerto → los métodos devuelven None/False
        monkeypatch.setattr(dm, "PORT_FILE", tmp_path / "nada.port")
        client = DaemonClient(timeout=0.2)
        assert client.ping() is False
        assert client.suggest("x") is None
        assert client.correct("x") is None
        assert client.contains("x") is None
        assert client.reload() is False
        assert is_available() is False


# ---------------------------------------------------------------------- #
# Estado en disco
# ---------------------------------------------------------------------- #
class TestState:
    def test_read_port(self, tmp_path, monkeypatch) -> None:
        p = tmp_path / "daemon.port"
        p.write_text("12345")
        monkeypatch.setattr(dm, "PORT_FILE", p)
        assert dm.read_port() == 12345

    def test_read_port_inexistente(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(dm, "PORT_FILE", tmp_path / "nada.port")
        assert dm.read_port() is None

    def test_read_port_corrupto(self, tmp_path, monkeypatch) -> None:
        p = tmp_path / "daemon.port"
        p.write_text("no-es-numero")
        monkeypatch.setattr(dm, "PORT_FILE", p)
        assert dm.read_port() is None

    def test_read_pid(self, tmp_path, monkeypatch) -> None:
        p = tmp_path / "daemon.pid"
        p.write_text("42")
        monkeypatch.setattr(dm, "PID_FILE", p)
        assert dm.read_pid() == 42

    def test_is_alive_falso_sin_archivo(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(dm, "PORT_FILE", tmp_path / "nada.port")
        assert dm.is_alive() is False

    def test_status_activo(self, daemon_server, capsys) -> None:
        rc = dm.status()
        out = capsys.readouterr().out
        assert rc == 0
        assert "ACTIVO" in out

    def test_status_detenido(self, tmp_path, monkeypatch, capsys) -> None:
        monkeypatch.setattr(dm, "PORT_FILE", tmp_path / "nada.port")
        monkeypatch.setattr(dm, "PID_FILE", tmp_path / "nada.pid")
        rc = dm.status()
        out = capsys.readouterr().out
        assert rc == 1
        assert "DETENIDO" in out


# ---------------------------------------------------------------------- #
# Handler de red con JSON inválido
# ---------------------------------------------------------------------- #
class TestHandler:
    def test_json_invalido(self, daemon_server) -> None:
        port = daemon_server.server_address[1]
        with socket.create_connection(("127.0.0.1", port), timeout=1) as s:
            s.sendall(b"esto no es json\n")
            data = s.recv(4096)
        assert b'"ok": false' in data or b'"ok":false' in data

    def test_conexion_sin_datos(self, daemon_server) -> None:
        port = daemon_server.server_address[1]
        with socket.create_connection(("127.0.0.1", port), timeout=1) as s:
            s.sendall(b"")  # cierre limpio
        # no debe lanzar