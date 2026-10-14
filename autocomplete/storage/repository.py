"""Persistencia con SQLAlchemy.

Por defecto usa SQLite en el directorio de configuración. Cambia a
PostgreSQL (o cualquier motor) solo con cambiar la URL:

    sqlite:///C:/Users/me/.autocomplete/data.db
    postgresql+psycopg://user:pass@localhost:5432/autocomplete
    mysql+pymysql://user:pass@localhost/autocomplete
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator, List, Optional, Tuple

from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from .models import Base, HistoryRecord, PreferenceRecord, WordRecord


class Storage:
    """Repositorio de palabras, historial y preferencias."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.engine = create_engine(url, future=True)
        Base.metadata.create_all(self.engine)
        self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    # ------------------------------------------------------------------ #
    # Sesiones
    # ------------------------------------------------------------------ #
    @contextmanager
    def _session(self) -> Iterator[Any]:
        s = self._session_factory()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    # ------------------------------------------------------------------ #
    # Detección de motor
    # ------------------------------------------------------------------ #
    @property
    def dialect(self) -> str:
        return self.engine.dialect.name.lower()

    @property
    def is_sqlite(self) -> bool:
        return self.dialect == "sqlite"

    @property
    def is_postgres(self) -> bool:
        return self.dialect in ("postgresql", "postgres")

    @property
    def is_mysql(self) -> bool:
        return self.dialect in ("mysql", "mariadb")

    # ------------------------------------------------------------------ #
    # Palabras
    # ------------------------------------------------------------------ #
    def add_word(self, text_: str, weight: int = 1, source: str = "manual") -> None:
        with self._session() as s:
            row = s.execute(
                select(WordRecord).where(WordRecord.text == text_)
            ).scalar_one_or_none()
            if row is None:
                s.add(WordRecord(text=text_, weight=weight, source=source))
            else:
                row.weight += weight
                row.source = source or row.source

    def add_many(self, items: Iterable[Tuple[str, int]], source: str = "bulk") -> int:
        count = 0
        with self._session() as s:
            for txt, weight in items:
                row = s.execute(
                    select(WordRecord).where(WordRecord.text == txt)
                ).scalar_one_or_none()
                if row is None:
                    s.add(WordRecord(text=txt, weight=weight, source=source))
                else:
                    row.weight += weight
                count += 1
        return count

    def all_words(self) -> List[Tuple[str, int]]:
        with self._session() as s:
            rows = s.execute(select(WordRecord)).scalars().all()
            return [(r.text, r.weight) for r in rows]

    def remove_word(self, text_: str) -> bool:
        with self._session() as s:
            row = s.execute(
                select(WordRecord).where(WordRecord.text == text_)
            ).scalar_one_or_none()
            if row is None:
                return False
            s.delete(row)
            return True

    def word_count(self) -> int:
        with self._session() as s:
            return s.query(WordRecord).count()

    # ------------------------------------------------------------------ #
    # Historial
    # ------------------------------------------------------------------ #
    def add_history(
        self,
        command: str,
        *,
        corrected: Optional[str] = None,
        executed: bool = False,
        exit_code: Optional[int] = None,
    ) -> None:
        with self._session() as s:
            s.add(
                HistoryRecord(
                    command=command,
                    corrected=corrected,
                    executed=executed,
                    exit_code=exit_code,
                )
            )

    def recent_history(self, limit: int = 20) -> List[HistoryRecord]:
        with self._session() as s:
            rows = (
                s.execute(
                    select(HistoryRecord)
                    .order_by(HistoryRecord.created_at.desc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
            return list(rows)

    def clear_history(self) -> int:
        with self._session() as s:
            n = s.query(HistoryRecord).count()
            s.query(HistoryRecord).delete()
            return n

    # ------------------------------------------------------------------ #
    # Preferencias
    # ------------------------------------------------------------------ #
    def get_pref(self, key: str, default: Any = None) -> Any:
        with self._session() as s:
            row = s.get(PreferenceRecord, key)
            if row is None:
                return default
            try:
                return json.loads(row.value)
            except json.JSONDecodeError:
                return row.value

    def set_pref(self, key: str, value: Any) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        with self._session() as s:
            row = s.get(PreferenceRecord, key)
            if row is None:
                s.add(PreferenceRecord(key=key, value=payload))
            else:
                row.value = payload

    def all_prefs(self) -> dict:
        with self._session() as s:
            rows = s.execute(select(PreferenceRecord)).scalars().all()
            out = {}
            for r in rows:
                try:
                    out[r.key] = json.loads(r.value)
                except json.JSONDecodeError:
                    out[r.key] = r.value
            return out

    # ------------------------------------------------------------------ #
    # Mantenimiento
    # ------------------------------------------------------------------ #
    def reset(self) -> None:
        """Elimina todas las filas de todas las tablas."""
        with self._session() as s:
            s.query(HistoryRecord).delete()
            s.query(PreferenceRecord).delete()
            s.query(WordRecord).delete()

    def _sqlite_path(self) -> Path:
        """Ruta al archivo .db de SQLite."""
        u = make_url(self.url)
        database = u.database or ""
        # Normaliza (Windows: "/C:/..." -> "C:/...")
        if database.startswith("/") and len(database) > 2 and database[2] == ":":
            database = database[1:]
        return Path(database)

    def backup(self, output: Optional[str] = None) -> Path:
        """Genera un respaldo de la base de datos.

        - SQLite: copia el archivo .db.
        - PostgreSQL: ``pg_dump``.
        - MySQL / MariaDB: ``mysqldump``.

        Returns:
            Ruta del archivo generado.
        """
        from ..config.settings import config_dir

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir = config_dir() / "backups"
        out_dir.mkdir(parents=True, exist_ok=True)

        if output is not None:
            target = Path(output).expanduser().resolve()
        else:
            ext = ".db" if self.is_sqlite else ".sql"
            target = out_dir / f"backup-{timestamp}{ext}"

        target.parent.mkdir(parents=True, exist_ok=True)

        if self.is_sqlite:
            src = self._sqlite_path()
            if not src.exists():
                raise FileNotFoundError(f"No existe la BD: {src}")
            # Forzar flush antes de copiar
            self.engine.dispose()
            shutil.copy2(src, target)
            return target

        u = make_url(self.url)
        host = u.host or "localhost"
        port = u.port
        user = u.username or ""
        password = u.password or ""
        dbname = (u.database or "").lstrip("/") or "postgres"

        if self.is_postgres:
            cmd = [
                "C:/Program Files/PostgreSQL/17/pgAdmin 4/runtime/pg_dump.exe",
                "-h",
                host,
                "-U",
                user,
                "-d",
                dbname,
                "-f",
                str(target),
            ]
            if port:
                cmd[3:3] = ["-p", str(port)]
            env = {**os.environ, "PGPASSWORD": password}
        elif self.is_mysql:
            cmd = ["mysqldump", "-h", host, "-u", user, f"-p{password}", dbname]
            env = os.environ.copy()
        else:
            raise NotImplementedError(
                f"Backup no soportado para motor {self.dialect!r}"
            )

        try:
            subprocess.run(cmd, check=True, env=env)
        except FileNotFoundError as exc:
            raise NotImplementedError(
                f"Herramienta '{cmd[0]}' no está en el PATH"
            ) from exc
        return target

    def restore(self, source: str) -> None:
        """Restaura un respaldo.

        - SQLite: reemplaza el archivo .db (recrea el engine).
        - PostgreSQL: ``psql -f``.
        - MySQL / MariaDB: ``mysql <``.
        """
        src = Path(source).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(f"No existe el backup: {src}")

        if self.is_sqlite:
            db_path = self._sqlite_path()
            self.engine.dispose()
            shutil.copy2(src, db_path)
            # Reabrir engine
            self.engine = create_engine(self.url, future=True)
            self._session_factory = sessionmaker(
                bind=self.engine, expire_on_commit=False
            )
            return

        u = make_url(self.url)
        host = u.host or "localhost"
        port = u.port
        user = u.username or ""
        password = u.password or ""
        dbname = (u.database or "").lstrip("/") or "postgres"

        if self.is_postgres:
            cmd = [
                "C:/Program Files/PostgreSQL/17/pgAdmin 4/runtime/psql.exe",
                "-h",
                host,
                "-U",
                user,
                "-d",
                dbname,
                "-f",
                str(src),
            ]
            if port:
                cmd[3:3] = ["-p", str(port)]
            env = {**os.environ, "PGPASSWORD": password}
            try:
                subprocess.run(cmd, check=True, env=env)
            except FileNotFoundError as exc:
                raise NotImplementedError(
                    "Herramienta 'psql' no está en el PATH"
                ) from exc
            return

        if self.is_mysql:
            cmd = ["mysql", "-h", host, "-u", user, f"-p{password}", dbname]
            env = os.environ.copy()
            try:
                with src.open("rb") as f:
                    subprocess.run(cmd, stdin=f, check=True, env=env)
            except FileNotFoundError as exc:
                raise NotImplementedError(
                    "Herramienta 'mysql' no está en el PATH"
                ) from exc
            return

        raise NotImplementedError(f"Restore no soportado para motor {self.dialect!r}")

    def vacuum(self) -> None:
        """Compacta la base de datos.

        - SQLite: ``VACUUM``
        - PostgreSQL: ``VACUUM FULL`` (requiere autocommit)
        - MySQL / MariaDB: ``OPTIMIZE TABLE`` en cada tabla
        """
        if self.is_sqlite:
            with self.engine.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as conn:
                conn.exec_driver_sql("VACUUM")
            return

        if self.is_postgres:
            with self.engine.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as conn:
                conn.exec_driver_sql("VACUUM FULL")
            return

        if self.is_mysql:
            tables = ["words", "history", "preferences"]
            with self.engine.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as conn:
                for t in tables:
                    conn.exec_driver_sql(f"OPTIMIZE TABLE {t}")
            return

        raise NotImplementedError(f"Vacuum no soportado para motor {self.dialect!r}")

    def db_size_bytes(self) -> Optional[int]:
        """Tamaño aproximado de la BD en bytes (solo SQLite)."""
        if not self.is_sqlite:
            return None
        p = self._sqlite_path()
        return p.stat().st_size if p.exists() else None

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def close(self) -> None:
        """Cierra el pool de conexiones del engine."""
        self.engine.dispose()

    def __enter__(self) -> "Storage":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        # Best-effort en el recolector
        try:
            self.engine.dispose()
        except Exception:  # noqa: BLE001
            pass
