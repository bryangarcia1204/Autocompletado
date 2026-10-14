"""Ejecución de comandos con logging opcional."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    command: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""

    @property
    def success(self) -> bool:
        return self.exit_code == 0


def run_command(
    command: str,
    *,
    timeout: Optional[float] = None,
    capture: bool = False,
    cwd: Optional[str] = None,
) -> ExecutionResult:
    """Ejecuta un comando usando el shell del sistema.

    Args:
        command: Línea de comando completa.
        timeout: Segundos máximos. ``None`` = sin timeout.
        capture: Si ``True``, captura stdout/stderr. Si ``False``,
            los hereda (útil para programas interactivos).
        cwd: Directorio de trabajo.
    """
    if capture:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return ExecutionResult(
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
        )

    proc = subprocess.run(command, shell=True, timeout=timeout, cwd=cwd)
    return ExecutionResult(command=command, exit_code=proc.returncode)
