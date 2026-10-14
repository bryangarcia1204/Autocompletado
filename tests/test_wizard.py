"""Tests del asistente `autocomplete init`."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from autocomplete.interfaces import wizard
from autocomplete.interfaces.wizard import (
    WRAPPERS,
    _append_line_once,
    _wrapper_text,
    detect_shell,
    profile_path,
)


class TestDetectShell:
    def test_no_explota(self, monkeypatch) -> None:
        monkeypatch.setenv("SHELL", "/bin/bash")
        shell = detect_shell()
        assert isinstance(shell, str)
        assert shell


class TestProfilePath:
    def test_bash(self) -> None:
        p = profile_path("bash")
        assert p is not None
        assert p.name == ".bashrc"

    def test_zsh(self) -> None:
        p = profile_path("zsh")
        assert p is not None
        assert p.name == ".zshrc"

    def test_fish(self) -> None:
        p = profile_path("fish")
        assert p is not None
        assert "fish" in str(p)

    def test_desconocido(self) -> None:
        assert profile_path("shell-raro") is None


class TestWrapperText:
    def test_ps1(self) -> None:
        content = _wrapper_text("wrapper.ps1")
        assert len(content) > 0

    def test_bash(self) -> None:
        content = _wrapper_text("wrapper.bash")
        assert "complete" in content or "_ac" in content

    def test_zsh(self) -> None:
        content = _wrapper_text("wrapper.zsh")
        assert len(content) > 0

    def test_fish(self) -> None:
        content = _wrapper_text("wrapper.fish")
        assert len(content) > 0

    def test_inexistente(self) -> None:
        with pytest.raises(FileNotFoundError):
            _wrapper_text("wrapper.xyz")


class TestAppendLineOnce:
    def test_append_nuevo(self, tmp_path: Path) -> None:
        profile = tmp_path / ".bashrc"
        added = _append_line_once(profile, "source x.sh", "test")
        assert added is True
        assert "source x.sh" in profile.read_text(encoding="utf-8")

    def test_append_duplicado(self, tmp_path: Path) -> None:
        profile = tmp_path / ".bashrc"
        _append_line_once(profile, "source x.sh", "test")
        added = _append_line_once(profile, "source x.sh", "test")
        assert added is False

    def test_crea_directorios_padre(self, tmp_path: Path) -> None:
        profile = tmp_path / "sub" / "dir" / ".bashrc"
        _append_line_once(profile, "linea", "test")
        assert profile.exists()


class TestWrappers:
    def test_todos_los_shells_mapeados(self) -> None:
        assert set(WRAPPERS.keys()) == {
            "pwsh",
            "powershell",
            "bash",
            "zsh",
            "fish",
        }


class TestRunInit:
    def test_no_interactivo(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        # Aislar config
        monkeypatch.setenv(
            "AUTOCOMPLETE_CONFIG", str(tmp_path / "config.json")
        )
        # No arrancar daemon real
        from autocomplete.server import daemon as dm

        monkeypatch.setattr(dm, "start_background", lambda: 0)
        # No instalar wrapper
        monkeypatch.setattr(
            wizard, "install_wrapper", lambda shell: None
        )

        rc = wizard.run_init(interactive=False)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Listo" in out