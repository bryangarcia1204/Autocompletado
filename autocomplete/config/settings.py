"""Configuración persistente del módulo autocomplete.

Ubicación por defecto:

- Windows : %APPDATA%\\autocomplete\\config.json
- Linux/mac: ~/.config/autocomplete/config.json

Sobreescribible con la variable de entorno AUTOCOMPLETE_CONFIG.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULTS: Dict[str, Any] = {
    "database_url": None,            # None = SQLite por defecto
    "auto_execute": False,           # ejecutar sin preguntar
    "confirm_before_execute": True,  # pedir confirmacion
    "max_distance": 2,
    "limit": 10,
    "remove_accents": True,
    "timeout": None,                 # segundos, None = sin timeout
}


def config_dir() -> Path:
    env = os.environ.get("AUTOCOMPLETE_CONFIG")
    if env:
        return Path(env).expanduser().resolve().parent
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "autocomplete"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "autocomplete"


def config_path() -> Path:
    env = os.environ.get("AUTOCOMPLETE_CONFIG")
    if env:
        return Path(env).expanduser()
    return config_dir() / "config.json"


def default_db_url() -> str:
    env = os.environ.get("AUTOCOMPLETE_DB_URL")
    if env:
        return env
    path = (config_dir() / "data.db").as_posix()
    return f"sqlite:///{path}"


class Config:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else config_path()
        self._data: Dict[str, Any] = dict(DEFAULTS)
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                stored = json.load(f)
            if isinstance(stored, dict):
                self._data.update(stored)
        except (OSError, json.JSONDecodeError):
            pass

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def reset(self) -> None:
        self._data = dict(DEFAULTS)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def db_url(self) -> str:
        return self.get("database_url") or default_db_url()