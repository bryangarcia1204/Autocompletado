# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [Unreleased]

### Added

- Nada todavía.

### Changed

- Nada todavía.

### Fixed

- Nada todavía.

---

## [1.0.0] - 2026-10-14

Primera versión publicable. Establece la API pública y la arquitectura
por capas del paquete.

### Added

**Núcleo (core)**

- `Autocomplete`: motor de autocompletado, autocorrección y carga masiva.
- `Trie` y `TrieNode`: estructura de datos interna con pesos.
- `similarity`: `levenshtein`, `damerau_levenshtein`, `find_similar`.
- `stats`: `LoadStats` y `LoadDirStats` para reportes de carga.

**Texto (text)**

- `strip_accents` y `normalize_key` con `unicodedata`.
- Búsqueda insensible a acentos (`"cafe"` encuentra `"café"`).

**Persistencia (storage)**

- Modelos SQLAlchemy 2.0: `WordRecord`, `HistoryRecord`, `PreferenceRecord`.
- `Storage` con CRUD de palabras, historial y preferencias.
- `backup`, `restore`, `vacuum`, `reset`, `db_size_bytes`.
- Soporte SQLite (por defecto), PostgreSQL y MySQL/MariaDB vía URL.

**Configuración (config)**

- `Config` en JSON con defaults y override por variables de entorno.
- Rutas por SO (`%APPDATA%` en Windows, `~/.config` en Linux/macOS).
- Variables `AUTOCOMPLETE_CONFIG` y `AUTOCOMPLETE_DB_URL`.

**Daemon (server)**

- Servidor TCP local que mantiene el Trie en memoria.
- Protocolo JSON delimitado por línea.
- Cliente `DaemonClient` con fallback silencioso al CLI.
- Archivos `daemon.port` y `daemon.pid` en el directorio de configuración.

**Ejecución (execution)**

- `run_command` y `ExecutionResult` con timeout y captura opcional.

**Interfaces**

- CLI con `argparse`:
  - `suggest`, `correct`, `shell`, `repl`
  - `load-dir`, `db`, `config`, `daemon`, `init`, `install-ps`
- API HTTP con FastAPI (`autocomplete.interfaces.api`).
- Asistente `autocomplete init` que detecta shell, instala wrappers,
  crea la BD y arranca el daemon.

**Wrappers (assets)**

- `wrapper.ps1` para PowerShell (PSReadLine 2.0+ y 2.3.x).
- `wrapper.bash`, `wrapper.zsh`, `wrapper.fish` para entornos POSIX.
- Todos daemon-aware con fallback al CLI.

**Diccionario**

- `comandos.txt` (~600 comandos en un archivo).
- `comandos/` con 28 archivos por categoría (~1300 comandos).

**Documentación y calidad**

- `README.md` con acta completa del proyecto.
- `CONTRIBUTING.md` con flujo de trabajo y convenciones.
- `CHANGELOG.md` (este archivo).
- `LICENSE` MIT.
- `py.typed` (marcador PEP 561).
- Suite de tests con `pytest`.

### Notas

- Python 3.9+.
- SQLAlchemy 2.0+ como única dependencia obligatoria.
- FastAPI, psycopg y pymysql como extras opcionales.

---

## Plantilla para nuevas entradas

Al publicar una versión nueva, copia esto debajo de `[Unreleased]`:

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