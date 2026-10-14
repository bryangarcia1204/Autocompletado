"""Daemon TCP local que mantiene el Trie cargado en memoria.

El wrapper de Tab se conecta a 127.0.0.1:<puerto> y pide sugerencias
mediante JSON delimitado por saltos de línea. El puerto se guarda en
``<config_dir>/daemon.port`` y el PID en ``<config_dir>/daemon.pid``.

Protocolo:
    -> {"op":"suggest","prefix":"git","limit":20}\n
    <- {"ok":true,"suggestions":["git","git-commit",...]}\n

Operaciones: ping, suggest, correct, contains, stats, reload, shutdown.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time
from typing import Any, Dict, Optional

from ..config.settings import Config, config_dir
from ..core.engine import Autocomplete
from ..storage.repository import Storage

PORT_FILE = config_dir() / "daemon.port"
PID_FILE = config_dir() / "daemon.pid"


# ---------------------------------------------------------------------- #
# Servidor
# ---------------------------------------------------------------------- #
class _Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        server: "DaemonServer" = self.server  # type: ignore[assignment]
        while True:
            line = self.rfile.readline()
            if not line:
                return
            try:
                req = json.loads(line.decode("utf-8"))
            except Exception as exc:  # noqa: BLE001
                self._send({"ok": False, "error": f"bad request: {exc}"})
                continue
            resp = server.dispatch(req)
            self._send(resp)
            if req.get("op") == "shutdown":
                threading.Thread(target=server.shutdown, daemon=True).start()
                return

    def _send(self, obj: Dict[str, Any]) -> None:
        self.wfile.write((json.dumps(obj) + "\n").encode("utf-8"))
        self.wfile.flush()


class DaemonServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ac: Optional[Autocomplete] = None
        self.storage: Optional[Storage] = None
        self.lock = threading.Lock()

    def load(self) -> None:
        cfg = Config()
        storage = None
        try:
            storage = Storage(cfg.db_url())
        except Exception:  # noqa: BLE001
            storage = None

        ac = Autocomplete(remove_accents=bool(cfg.get("remove_accents", True)))
        if storage is not None:
            for text, weight in storage.all_words():
                ac.add_word(text, weight=weight)

        with self.lock:
            self.ac = ac
            self.storage = storage

    def dispatch(self, req: Dict[str, Any]) -> Dict[str, Any]:
        op = req.get("op")
        try:
            if op == "ping":
                return {"ok": True, "pong": True, "version": 1}
            if op == "shutdown":
                return {"ok": True, "shutdown": True}
            if op == "reload":
                self.load()
                return {"ok": True, "reloaded": True}

            with self.lock:
                ac = self.ac
            if ac is None:
                return {"ok": False, "error": "not loaded"}

            if op == "suggest":
                return {
                    "ok": True,
                    "suggestions": ac.suggestions(
                        req["prefix"],
                        limit=req.get("limit"),
                        sort_by_frequency=req.get("sort_by_frequency", True),
                    ),
                }
            if op == "correct":
                res = ac.correct(
                    req["word"],
                    max_distance=req.get("max_distance", 2),
                    limit=req.get("limit", 10),
                )
                return {"ok": True, "corrections": [[w, d] for w, d in res]}
            if op == "contains":
                return {"ok": True, "contains": ac.contains(req["word"])}
            if op == "stats":
                return {"ok": True, "words": len(ac)}
            return {"ok": False, "error": f"unknown op {op!r}"}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------- #
# Estado en disco
# ---------------------------------------------------------------------- #
def _write_state(port: int) -> None:
    config_dir().mkdir(parents=True, exist_ok=True)
    PORT_FILE.write_text(str(port), encoding="utf-8")
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def _cleanup_state() -> None:
    for f in (PORT_FILE, PID_FILE):
        try:
            f.unlink()
        except FileNotFoundError:
            pass


def read_port() -> Optional[int]:
    try:
        return int(PORT_FILE.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def read_pid() -> Optional[int]:
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def is_alive(port: Optional[int] = None) -> bool:
    port = port or read_port()
    if port is None:
        return False
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5) as s:
            s.sendall(b'{"op":"ping"}\n')
            data = s.recv(1024)
            return b'"pong"' in data
    except OSError:
        return False


# ---------------------------------------------------------------------- #
# Ciclo de vida
# ---------------------------------------------------------------------- #
def run_server(host: str = "127.0.0.1", port: int = 0) -> int:
    server = DaemonServer((host, port), _Handler)
    real_port = server.server_address[1]
    _write_state(real_port)
    server.load()

    def _stop(signum, frame):  # noqa: ARG001
        threading.Thread(target=server.shutdown, daemon=True).start()

    for sig in ("SIGTERM", "SIGINT"):
        try:
            signal.signal(getattr(signal, sig), _stop)
        except (ValueError, AttributeError):
            pass

    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        _cleanup_state()
        server.server_close()
    return 0


def start_background() -> int:
    if is_alive():
        print("El daemon ya está corriendo.")
        return 0

    cmd = [sys.executable, "-m", "autocomplete", "daemon", "run"]
    kwargs = dict(
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    if sys.platform == "win32":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    subprocess.Popen(cmd, **kwargs)

    deadline = time.time() + 5
    while time.time() < deadline:
        if is_alive():
            print(f"Daemon iniciado. Puerto: {read_port()}")
            return 0
        time.sleep(0.1)

    print("El daemon no respondió en 5 segundos.", file=sys.stderr)
    return 1


def stop_background() -> int:
    port = read_port()
    if port is None:
        print("El daemon no está corriendo.")
        return 0

    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1) as s:
            s.sendall(b'{"op":"shutdown"}\n')
            s.recv(1024)
    except OSError:
        pass

    deadline = time.time() + 3
    while time.time() < deadline:
        if not is_alive(port):
            _cleanup_state()
            print("Daemon detenido.")
            return 0
        time.sleep(0.1)

    pid = read_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    _cleanup_state()
    print("Daemon detenido (forzado).")
    return 0


def status() -> int:
    if is_alive():
        print(f"Daemon ACTIVO  puerto={read_port()}  pid={read_pid()}")
        return 0
    print("Daemon DETENIDO.")
    return 1


def reload_if_running() -> None:
    """Pide al daemon que recargue desde la BD. Silencioso si no corre."""
    from ..server.client import DaemonClient

    c = DaemonClient()
    if c.ping():
        c.reload()
