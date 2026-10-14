"""Tests de la configuración persistente."""

from __future__ import annotations

import json
from pathlib import Path

from autocomplete import Config
from autocomplete.config import settings as cfg_mod
from autocomplete.config.settings import DEFAULTS


class TestConfig:
    def test_defaults(self, tmp_path: Path) -> None:
        cfg = Config(tmp_path / "config.json")
        assert cfg.get("max_distance") == 2
        assert cfg.get("limit") == 10
        assert cfg.get("remove_accents") is True

    def test_set_y_get(self, tmp_path: Path) -> None:
        cfg = Config(tmp_path / "config.json")
        cfg.set("max_distance", 3)
        assert cfg.get("max_distance") == 3

    def test_save_y_load(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        cfg = Config(path)
        cfg.set("auto_execute", True)
        cfg.save()

        assert path.exists()
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        assert data["auto_execute"] is True

        cfg2 = Config(path)
        assert cfg2.get("auto_execute") is True

    def test_reset(self, tmp_path: Path) -> None:
        cfg = Config(tmp_path / "config.json")
        cfg.set("max_distance", 99)
        cfg.reset()
        assert cfg.get("max_distance") == DEFAULTS["max_distance"]

    def test_as_dict(self, tmp_path: Path) -> None:
        cfg = Config(tmp_path / "config.json")
        d = cfg.as_dict()
        assert isinstance(d, dict)
        assert "database_url" in d

    def test_db_url_default_sqlite(self, tmp_path: Path) -> None:
        cfg = Config(tmp_path / "config.json")
        url = cfg.db_url()
        assert url.startswith("sqlite:///")

    def test_db_url_custom(self, tmp_path: Path) -> None:
        cfg = Config(tmp_path / "config.json")
        cfg.set("database_url", "postgresql+psycopg://u:p@h/db")
        assert cfg.db_url() == "postgresql+psycopg://u:p@h/db"

    def test_archivo_corrupto_no_rompe(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text("esto no es json", encoding="utf-8")
        cfg = Config(path)  # no debe lanzar
        assert cfg.get("max_distance") == 2


class TestConfigPath:
    def test_env_var_override(self, tmp_path, monkeypatch) -> None:
        target = tmp_path / "custom.json"
        monkeypatch.setenv("AUTOCOMPLETE_CONFIG", str(target))
        assert cfg_mod.config_path() == target

    def test_config_dir_con_env(self, tmp_path, monkeypatch) -> None:
        target = tmp_path / "sub" / "config.json"
        monkeypatch.setenv("AUTOCOMPLETE_CONFIG", str(target))
        assert cfg_mod.config_dir() == tmp_path / "sub"


class TestDefaultDbUrl:
    def test_env_var(self, monkeypatch) -> None:
        monkeypatch.setenv("AUTOCOMPLETE_DB_URL", "postgresql://x/y")
        assert cfg_mod.default_db_url() == "postgresql://x/y"

    def test_sin_env(self, tmp_path, monkeypatch) -> None:
        monkeypatch.delenv("AUTOCOMPLETE_DB_URL", raising=False)
        monkeypatch.setenv(
            "AUTOCOMPLETE_CONFIG", str(tmp_path / "config.json")
        )
        url = cfg_mod.default_db_url()
        assert url.startswith("sqlite:///")