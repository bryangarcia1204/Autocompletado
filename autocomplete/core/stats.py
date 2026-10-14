"""Estadísticas de carga masiva."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LoadStats:
    """Estadísticas devueltas por ``Autocomplete.bulk_load``."""

    loaded: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Total de líneas procesadas."""
        return self.loaded + self.skipped

    def __str__(self) -> str:
        return (
            f"LoadStats(loaded={self.loaded}, skipped={self.skipped}, "
            f"errors={len(self.errors)})"
        )


@dataclass
class LoadDirStats:
    """Estadísticas combinadas de ``Autocomplete.bulk_load_dir``."""

    files: Dict[str, LoadStats] = field(default_factory=dict)

    @property
    def loaded(self) -> int:
        return sum(s.loaded for s in self.files.values())

    @property
    def skipped(self) -> int:
        return sum(s.skipped for s in self.files.values())

    @property
    def errors(self) -> List[str]:
        out: List[str] = []
        for name, s in self.files.items():
            for e in s.errors:
                out.append(f"[{name}] {e}")
        return out

    @property
    def total_files(self) -> int:
        return len(self.files)

    def __str__(self) -> str:
        return (
            f"LoadDirStats(files={self.total_files}, loaded={self.loaded}, "
            f"skipped={self.skipped}, errors={len(self.errors)})"
        )
