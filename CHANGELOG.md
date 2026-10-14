# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

Tipos de cambios:

- **Added**: nuevas funcionalidades.
- **Changed**: cambios en funcionalidad existente.
- **Deprecated**: funcionalidad a punto de eliminarse.
- **Removed**: funcionalidad eliminada.
- **Fixed**: correcciones de bugs.
- **Security**: vulnerabilidades corregidas.

---

## [Unreleased]

### Added

- Documentación de integración con FastAPI, Flask y Django en `README.md`.
- `CONTRIBUTING.md` con convenciones de commits, código y flujo de PRs.
- `CHANGELOG.md` con historial completo.
- `LICENSE` MIT.

### Changed

- Nada todavía.

### Fixed

- Nada todavía.

---

## [1.5.0] - 2026-10-14

### Added

- `db restore <archivo>` para restaurar un respaldo previo. Pide
  confirmación salvo `--yes`.
- `db vacuum` para compactar la BD. Usa `VACUUM` en SQLite,
  `VACUUM FULL` en PostgreSQL, `OPTIMIZE TABLE` en MySQL.
- `db history --clear` para vaciar el historial.
- `db info` muestra el motor (`SQLite`, `PostgreSQL`, etc.) y el tamaño
  del archivo en SQLite.
- `Storage.dialect`, `Storage.is_sqlite`, `Storage.is_postgres`,
  `Storage.is_mysql` como propiedades.
- `Storage.reset()`, `Storage.backup()`, `Storage.restore()`,
  `Storage.vacuum()`, `Storage.db_size_bytes()`,
  `Storage.clear_history()`.
- `Storage._sqlite_path()` maneja rutas Windows (`C:/...`).
- `Autocomplete.bulk_load_dir()` para cargar directorios completos.
- `LoadDirStats` con estadísticas por archivo.
- `autocomplete load-dir <dir>` con `--pattern`, `--recursive`,
  `--replace`.
- Diccionario `comandos/` con 28 archivos por categoría (~1300 comandos).

### Changed

- `db backup` detecta el motor y usa copia directa en SQLite,
  `pg_dump` en PostgreSQL, `mysqldump` en MySQL.
- `db restart` avisa al daemon para recargar el Trie.
- `db add` y `db remove` notifican al daemon tras cada cambio.

### Fixed

- Rutas SQLite en Windows que empezaban con `/C:/...` ya se normalizan.

---

## [1.4.0] - 2026-10-14

### Added

- Daemon TCP local (`daemon.py`) que mantiene el Trie en memoria.
- Cliente del daemon (`client.py`) con fallback al CLI.
- Subcomandos `daemon start|stop|status|reload|restart|run`.
- Archivo de puerto `<config_dir>/daemon.port` y PID
  `<config_dir>/daemon.pid`.
- Asistente `autocomplete init` (`init_wizard.py`) que detecta el shell,
  instala wrappers, crea la BD y arranca el daemon.
- `autocomplete init --yes` para modo no interactivo.
- Wrappers daemon-aware:
  - `wrapper.ps1` (PowerShell)
  - `wrapper.bash`
  - `wrapper.zsh`
  - `wrapper.fish`
- Comando `autocomplete install-ps`.
- Auto-reload del daemon al añadir o quitar palabras por CLI.

### Changed

- El subcomando `suggest` usa el daemon si está activo; si no, cae al
  CLI.
- El wrapper de PowerShell ya no intercepta `Enter` (evita el error de
  `PSReadLine` en versiones 2.0.0).

### Fixed

- `No se encuentra el tipo [Microsoft.PowerShell.PSReadLine]` al
  cargar el wrapper en Windows PowerShell 5.1.

---

## [1.3.0] - 2026-10-14

### Added

- Persistencia con SQLAlchemy 2.0 (`storage.py`).
- Modelos `WordRecord`, `HistoryRecord`, `PreferenceRecord`.
- Subcomando `db` con `init`, `info`, `add`, `remove`, `list`,
  `history`.
- Subcomando `load-dir` para cargar directorios a la BD.
- Subcomando `config` con `show`, `path`, `set`, `reset`.
- Configuración JSON persistente en `%APPDATA%\autocomplete\config.json`
  (Windows) o `~/.config/autocomplete/config.json` (Linux/macOS).
- Variables de entorno `AUTOCOMPLETE_CONFIG` y `AUTOCOMPLETE_DB_URL`.
- Tabla `history` que registra cada comando ejecutado por `shell`.
- Tabla `preferences` que sincroniza con el JSON.
- Soporte PostgreSQL (`psycopg[binary]`) y MySQL (`pymysql`) como
  extras opcionales.

### Changed

- La URL de BD se lee desde `--db-url`, variable de entorno o config.
- El subcomando `shell` guarda historial en la BD si está disponible.

---

## [1.2.0] - 2026-10-14

### Added

- CLI con `argparse` (`cli.py`).
- Subcomandos `suggest`, `correct`, `shell`, `repl`.
- Módulo `similarity.py` con `levenshtein`, `damerau_levenshtein` y
  `find_similar`.
- Método `Autocomplete.correct()` con Damerau-Levenshtein.
- Método `Autocomplete.all_words()`.
- Módulo `executor.py` con `run_command()` y `ExecutionResult`.
- Modo `shell` con ejecución de comandos y confirmación.
- Flags `--execute`, `--yes`, `--dry-run`.
- Entry point `autocomplete` en `pyproject.toml`.
- `__main__.py` para `python -m autocomplete`.

### Changed

- `pip install -e .` ahora registra el comando global `autocomplete`.
- `pyproject.toml` incluye `[project.scripts]`.

---

## [1.1.0] - 2026-10-14

### Added

- Normalización de acentos con `unicodedata` (`text_utils.py`).
- `strip_accents()` y `normalize_key()`.
- `Autocomplete.bulk_load()` para cargar `.txt`, `.tsv` y `.gz`.
- `Autocomplete.from_file()` como constructor alternativo.
- `LoadStats` con `loaded`, `skipped`, `errors`.
- Soporte para comentarios con prefijo configurable (`#` por defecto).
- Columna de pesos configurable con `weight_column`.
- Callback `on_progress` en `bulk_load`.
- Tests de acentos, `bulk_load` y errores.
- Estructura de paquete (`autocomplete/`) con submódulos.
- `pyproject.toml` para instalación editable.

### Changed

- El Trie usa claves normalizadas pero preserva la palabra original.
- `suggestions` devuelve palabras con su forma original.
- `remove_word` poda nodos vacíos del Trie.

### Fixed

- Orden de sugerencias con acentos ahora es consistente (usa
  `strip_accents` en el desempate).
- `contains` ya no es sensible a mayúsculas.

---

## [1.0.0] - 2026-10-13

### Added

- Versión inicial.
- Clase `Autocomplete` con Trie.
- Métodos `add_word`, `add_words`, `remove_word`, `contains`,
  `suggestions`.
- Orden por frecuencia con desempate alfabético.
- `TrieNode` con `children` y `words`.
- `Trie` interno con `insert`, `find_node`, `contains`, `remove`,
  `iter_words`.
- Excepciones `AutocompleteError`, `InvalidWordError`,
  `InvalidPrefixError`.
- Diccionario de ejemplo `comandos.txt`.
- Tests básicos con `pytest`.
- `README.md` con uso básico.

---

## Plantilla para nuevas entradas

Al añadir una nueva versión, copia esto al inicio del archivo (debajo
de `[Unreleased]`):

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added

- ...

### Changed

- ...

### Deprecated

- ...

### Removed

- ...

### Fixed

- ...

### Security

- ...
```

---

## Enlaces de comparación

Al publicar una versión, añade el enlace al final:

```markdown
[Unreleased]: https://github.com/<org>/autocomplete/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/<org>/autocomplete/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/<org>/autocomplete/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/<org>/autocomplete/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/<org>/autocomplete/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/<org>/autocomplete/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/<org>/autocomplete/releases/tag/v1.0.0
```