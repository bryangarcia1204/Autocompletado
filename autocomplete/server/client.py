"""Cliente del daemon. Fallback silencioso si no está corriendo."""

from __future__ import annotations

import json
import socket
from typing import Any, Dict, List, Optional, Tuple

from ..server.daemon import is_alive, read_port


class DaemonClient:
    """Cliente síncrono. Todos los métodos devuelven ``None`` si fallan."""

    def __init__(self, timeout: float = 0.3) -> None:
        self.timeout = timeout

    def _call(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        port = read_port()
        if port is None:
            return None
        try:
            with socket.create_connection(
                ("127.0.0.1", port), timeout=self.timeout
            ) as s:
                s.sendall((json.dumps(req) + "\n").encode("utf-8"))
                buf = b""
                while not buf.endswith(b"\n"):
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                if not buf:
                    return None
                return json.loads(buf.decode("utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def ping(self) -> bool:
        r = self._call({"op": "ping"})
        return bool(r and r.get("ok"))

    def suggest(
        self, prefix: str, limit: Optional[int] = None
    ) -> Optional[List[str]]:
        r = self._call({"op": "suggest", "prefix": prefix, "limit": limit})
        if not r or not r.get("ok"):
            return None
        return r.get("suggestions")

    def correct(
        self, word: str, max_distance: int = 2, limit: int = 10
    ) -> Optional[List[Tuple[str, int]]]:
        r = self._call(
            {
                "op": "correct",
                "word": word,
                "max_distance": max_distance,
                "limit": limit,
            }
        )
        if not r or not r.get("ok"):
            return None
        return [(w, d) for w, d in r.get("corrections", [])]

    def contains(self, word: str) -> Optional[bool]:
        r = self._call({"op": "contains", "word": word})
        if not r or not r.get("ok"):
            return None
        return r.get("contains")

    def reload(self) -> bool:
        r = self._call({"op": "reload"})
        return bool(r and r.get("ok"))


def is_available() -> bool:
    return is_alive()