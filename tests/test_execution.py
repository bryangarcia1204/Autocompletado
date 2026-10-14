"""Tests del ejecutor de comandos."""

from __future__ import annotations

import subprocess
import sys

import pytest

from autocomplete import ExecutionResult, run_command

# Comando "no-op" que siempre devuelve 0 en cualquier SO
NOOP = "ver > nul" if sys.platform == "win32" else "true"
FAIL = "exit /b 1" if sys.platform == "win32" else "false"
ECHO = "echo hola"


class TestRunCommand:
    def test_success(self) -> None:
        result = run_command(NOOP, capture=True)
        assert isinstance(result, ExecutionResult)
        assert result.exit_code == 0
        assert result.success is True

    def test_failure(self) -> None:
        result = run_command(FAIL, capture=True)
        assert result.exit_code != 0
        assert result.success is False

    def test_capture_true(self) -> None:
        result = run_command(ECHO, capture=True)
        assert "hola" in result.stdout

    def test_capture_false(self) -> None:
        result = run_command(NOOP, capture=False)
        assert result.exit_code == 0
        # Sin captura, stdout/stderr quedan vacíos
        assert result.stdout == ""
        assert result.stderr == ""

    def test_timeout(self) -> None:
        slow = "ping 127.0.0.1 -n 30 > nul" if sys.platform == "win32" else "sleep 5"
        with pytest.raises(subprocess.TimeoutExpired):
            run_command(slow, timeout=0.4)

    def test_cwd(self, tmp_path) -> None:
        listar = "dir /b" if sys.platform == "win32" else "ls"
        result = run_command(listar, capture=True, cwd=str(tmp_path))
        assert result.exit_code == 0

    def test_command_en_resultado(self) -> None:
        result = run_command(NOOP, capture=True)
        assert result.command == NOOP


class TestExecutionResult:
    def test_success_true(self) -> None:
        assert ExecutionResult("x", 0).success is True

    def test_success_false(self) -> None:
        assert ExecutionResult("x", 1).success is False