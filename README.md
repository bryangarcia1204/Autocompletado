# autocomplete

Paquete Python reutilizable de autocompletado, autocorrección y
sugerencia de comandos basado en Trie. Incluye CLI, daemon TCP local,
Tab wrapper para PowerShell/bash/zsh/fish, persistencia con SQLAlchemy
y soporte para integrarse como librería embebida en otros proyectos
(scripts, generadores de documentos, servicios web).

---

## Tabla de contenidos

1. [Descripción](#descripción)
2. [Requerimientos](#requerimientos)
3. [Instalación](#instalación)
4. [Estructura del proyecto](#estructura-del-proyecto)
5. [Uso básico como librería](#uso-básico-como-librería)
6. [CLI](#cli)
7. [Configuración persistente](#configuración-persistente)
8. [Base de datos](#base-de-datos)
9. [Daemon](#daemon)
10. [Tab wrapper](#tab-wrapper)
11. [Asistente `init`](#asistente-init)
12. [Diccionario de comandos](#diccionario-de-comandos)
13. [Integración en otros proyectos](#integración-en-otros-proyectos)
14. [Tests](#tests)
15. [Solución de problemas](#solución-de-problemas)
16. [Licencia](#licencia)

---

## Descripción

`autocomplete` ofrece:

- **Autocompletado por prefijo** (Trie con pesos/frecuencia).
- **Autocorrección** de typos (distancia Damerau-Levenshtein).
- **Normalización de acentos**: `"cafe"` encuentra `"café"`.
- **Carga masiva** desde `.txt`, `.tsv`, `.gz` y directorios completos.
- **Persistencia** con SQLAlchemy 2.0: SQLite por defecto,
  PostgreSQL/MySQL cambiando solo la URL.
- **CLI** con subcomandos (`suggest`, `correct`, `shell`, `repl`,
  `load-dir`, `db`, `config`, `daemon`, `init`, `install-ps`).
- **Daemon TCP local** para que el Tab responda en ~5-15 ms.
- **Tab wrapper** para PowerShell, bash, zsh y fish (daemon-aware).
- **API HTTP** opcional vía FastAPI.

---

## Requerimientos

### Software base

- **Python 3.9+** (probado en 3.13).
- **SQLAlchemy 2.0+** (única dependencia obligatoria).

### Opcional

- `psycopg[binary]>=3.1` para PostgreSQL.
- `pymysql>=1.1` para MySQL/MariaDB.
- `fastapi[standard]` + `uvicorn` para el API HTTP.
- `pytest>=7` + `pytest-cov` para tests.

### Shell soportado para el Tab wrapper

- **PowerShell 5.1+** o **PowerShell 7+** con PSReadLine 2.0+.
- **bash**, **zsh**, **fish** en Linux/macOS.

### Herramientas del sistema (solo para backup/restore de PostgreSQL/MySQL)

- PostgreSQL: `pg_dump` y `psql`.
- MySQL/MariaDB: `mysqldump` y `mysql`.

No es necesario tenerlas en el PATH: ver
[Backup y restore](#backup-y-restore).

---

## Instalación

### 1. Clonar y entrar

```powershell
git clone <url-del-repo>
cd Autocompletado
```

### 2. Entorno virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instalar en modo editable

```powershell
pip install -e .
```

Con extras opcionales:

```powershell
pip install -e ".[dev,postgres]"
```

### 4. Verificar

```powershell
python -m autocomplete -h
```

Debe imprimir la ayuda del CLI.

> **Importante**: usar `python -m autocomplete`, **no** `python autocomplete`.
> Ver [Solución de problemas](#solución-de-problemas).

---

## Estructura del proyecto

```text
Autocompletado/
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
├── .editorconfig
├── comandos.txt                    # diccionario monolítico
├── comandos/                       # diccionario por categorías
│   ├── 01-git.txt
│   ├── 02-docker.txt
│   ├── ... (28 archivos)
│   └── 28-devops.txt
├── autocomplete/
│   ├── __init__.py                 # API pública (re-exports)
│   ├── __main__.py                 # entry point `python -m autocomplete`
│   ├── py.typed                    # marcador PEP 561
│   ├── exceptions.py
│   │
│   ├── core/                       # dominio, sin I/O
│   │   ├── __init__.py
│   │   ├── engine.py               # clase Autocomplete
│   │   ├── trie.py                 # Trie + TrieNode
│   │   ├── similarity.py           # levenshtein / damerau
│   │   └── stats.py                # LoadStats / LoadDirStats
│   │
│   ├── text/
│   │   ├── __init__.py
│   │   └── normalization.py        # strip_accents, normalize_key
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── models.py               # Base + modelos ORM
│   │   └── repository.py           # Storage (CRUD + mantenimiento)
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # Config + rutas por SO
│   │
│   ├── server/
│   │   ├── __init__.py
│   │   ├── daemon.py               # servidor TCP
│   │   └── client.py               # cliente con fallback
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   └── runner.py               # run_command, ExecutionResult
│   │
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── cli.py                  # CLI argparse
│   │   └── wizard.py               # asistente `init`
│   │
│   └── assets/
│       ├── __init__.py
│       ├── wrapper.ps1
│       ├── wrapper.bash
│       ├── wrapper.zsh
│       └── wrapper.fish
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_bulk_load.py
    ├── test_cli.py
    ├── test_config.py
    ├── test_core.py
    ├── test_execution.py
    ├── test_server.py
    ├── test_similarity.py
    ├── test_stats.py
    ├── test_storage.py
    ├── test_text.py
    └── test_wizard.py
```

### Reglas de dependencia entre capas

Cada capa puede importar de las inferiores, nunca al revés. `core` es
testeable sin base de datos ni red.

```text
interfaces  →  server / execution / storage / config
                ↓
              core  ←  text
                ↓
           exceptions
```

| Capa | Responsabilidad | Puede importar de |
|---|---|---|
| `interfaces` | Puntos de entrada (CLI, wizard) | Todo lo demás |
| `server` | Daemon TCP y cliente | `core`, `storage`, `config` |
| `execution` | Ejecución de comandos | `exceptions` |
| `storage` | Persistencia SQLAlchemy | `config`, `exceptions` |
| `config` | Configuración JSON | `exceptions` |
| `core` | Lógica pura del Trie y motor | `text`, `exceptions` |
| `text` | Normalización de texto | `exceptions` |
| `exceptions` | Excepciones | — |

### Mapa de módulos

| Archivo | Responsabilidad |
|---|---|
| `core/engine.py` | Clase `Autocomplete` |
| `core/trie.py` | `Trie`, `TrieNode` |
| `core/similarity.py` | `levenshtein`, `damerau_levenshtein`, `find_similar` |
| `core/stats.py` | `LoadStats`, `LoadDirStats` |
| `text/normalization.py` | `strip_accents`, `normalize_key` |
| `storage/models.py` | `Base`, `WordRecord`, `HistoryRecord`, `PreferenceRecord` |
| `storage/repository.py` | Clase `Storage` (CRUD, backup, restore, vacuum, reset) |
| `config/settings.py` | Clase `Config`, `config_dir`, `config_path`, `default_db_url` |
| `server/daemon.py` | Servidor TCP con Trie en memoria |
| `server/client.py` | `DaemonClient` con fallback silencioso |
| `execution/runner.py` | `run_command`, `ExecutionResult` |
| `interfaces/cli.py` | Parser argparse y handlers |
| `interfaces/wizard.py` | Asistente `autocomplete init` |

---

## Uso básico como librería

```python
from autocomplete import Autocomplete

ac = Autocomplete(["casa", "casamiento", "casco"])

print(ac.suggestions("cas"))
# ['casa', 'casamiento', 'casco']

print(ac.suggestions("cas", limit=2))
# ['casa', 'casamiento']

# Autocorrección
print(ac.correct("casaa"))
# [('casa', 1)]

# Con acentos
ac2 = Autocomplete(["café", "cafetería", "cama"])
print(ac2.suggestions("cafe"))
# ['cafetería', 'café']
```

### API pública del paquete

```python
from autocomplete import (
    Autocomplete,        # clase principal
    LoadStats,           # stats de bulk_load
    LoadDirStats,        # stats de bulk_load_dir
    Trie,                # estructura interna
    TrieNode,
    Config,              # configuración persistente
    Storage,             # persistencia SQLAlchemy
    Base,
    WordRecord,
    HistoryRecord,
    PreferenceRecord,
    ExecutionResult,     # resultado de run_command
    run_command,         # ejecutor de comandos
    strip_accents,       # normalización
    normalize_key,
    levenshtein,
    damerau_levenshtein,
    find_similar,
    AutocompleteError,
    InvalidWordError,
    InvalidPrefixError,
)
```

### Métodos de `Autocomplete`

| Método | Descripción |
|---|---|
| `add_word(word, weight=1)` | Añade una palabra con peso |
| `add_words(iterable \| dict)` | Añade varias palabras |
| `remove_word(word)` | Elimina una palabra |
| `contains(word)` | ¿Existe la palabra? |
| `suggestions(prefix, limit=None, sort_by_frequency=True)` | Sugerencias por prefijo |
| `correct(word, max_distance=2, limit=5)` | Autocorrección |
| `all_words()` | Itera todas las palabras |
| `bulk_load(source, ...)` | Carga desde archivo |
| `bulk_load_dir(dir, ...)` | Carga desde directorio |
| `from_file(path, ...)` | Constructor alternativo |
| `__len__` | Número de palabras |
| `__contains__` | `"x" in ac` |

---

## CLI

Ejecutable con `python -m autocomplete` o `autocomplete` (si está
instalado con `pip install -e .`).

### Subcomandos

| Comando | Descripción |
|---|---|
| `suggest <prefix>` | Sugiere palabras por prefijo |
| `correct <word>` | Corrige un typo |
| `shell` | Autocorrector interactivo con ejecución |
| `repl` | Explorador interactivo (solo sugiere) |
| `load-dir <dir>` | Carga directorio a la BD |
| `config` | Ver/editar preferencias |
| `db` | Operaciones sobre la BD |
| `daemon` | Gestión del daemon |
| `init` | Asistente de configuración |
| `install-ps` | Instala wrapper PowerShell |

### Argumentos globales

```text
-f, --file FILE         Archivo a cargar (.txt/.tsv/.gz)
--encoding ENCODING     Codificación (default: utf-8)
--separator SEP         Separador de columnas (\t, ",", etc.)
--db-url URL            URL SQLAlchemy
--no-db                 No usar BD
--no-accents            Desactiva normalización de acentos
--no-daemon             No usar el daemon aunque esté corriendo
```

El flag `--no-daemon` es útil para scripting: garantiza que el CLI
resuelva las sugerencias localmente sin depender del estado del daemon.

### Ejemplos

```powershell
# Sugerencias
python -m autocomplete -f comandos.txt suggest git --limit 5

# Corrección y ejecución
python -m autocomplete correct gti -x --rest "status" --yes

# Autocorrector interactivo
python -m autocomplete shell --yes

# Cargar directorio
python -m autocomplete load-dir comandos --recursive --replace

# Forzar uso local sin daemon
python -m autocomplete --no-daemon suggest git
```

### Subcomandos `db`

| Comando | Descripción |
|---|---|
| `db init` | Inicializa la BD |
| `db info` | Muestra URL, motor, número de palabras y tamaño |
| `db add <words...>` | Añade palabras |
| `db remove <words...>` | Elimina palabras |
| `db list [--limit N]` | Lista palabras |
| `db history [--limit N] [--clear]` | Historial |
| `db restart [--yes]` | Borra todos los datos |
| `db backup [-o FILE]` | Genera respaldo |
| `db restore <file> [--yes]` | Restaura respaldo |
| `db vacuum` | Compacta la BD |

### Subcomandos `daemon`

| Comando | Descripción |
|---|---|
| `daemon run` | Corre en primer plano |
| `daemon start` | Arranca en background |
| `daemon stop` | Detiene el daemon |
| `daemon status` | Estado actual |
| `daemon reload` | Recarga palabras desde la BD |
| `daemon restart` | Reinicia |

---

## Configuración persistente

Ubicación:

- **Windows**: `%APPDATA%\autocomplete\config.json`
- **Linux/macOS**: `~/.config/autocomplete/config.json`

Sobreescribible con la variable de entorno `AUTOCOMPLETE_CONFIG`.

### Preferencias por defecto

```json
{
  "database_url": null,
  "auto_execute": false,
  "confirm_before_execute": true,
  "max_distance": 2,
  "limit": 10,
  "remove_accents": true,
  "timeout": null
}
```

### Gestión

```powershell
python -m autocomplete config show
python -m autocomplete config path
python -m autocomplete config set auto_execute true
python -m autocomplete config set database_url "postgresql+psycopg://user:pass@host/db"
python -m autocomplete config reset
```

### Variables de entorno

| Variable | Uso |
|---|---|
| `AUTOCOMPLETE_CONFIG` | Ruta al `config.json` |
| `AUTOCOMPLETE_DB_URL` | Sobreescribe `database_url` |
| `AUTOCOMPLETE_PG_DUMP` | Ruta explícita a `pg_dump` |
| `AUTOCOMPLETE_MYSQLDUMP` | Ruta explícita a `mysqldump` |

---

## Base de datos

### Motor por defecto: SQLite

Se crea en `<config_dir>/data.db` automáticamente al primer uso.

### Cambiar a PostgreSQL

```powershell
pip install "psycopg[binary]"
python -m autocomplete config set database_url "postgresql+psycopg://user:pass@localhost:5432/autocomplete"
python -m autocomplete db init
```

### Cambiar a MySQL/MariaDB

```powershell
pip install pymysql
python -m autocomplete config set database_url "mysql+pymysql://user:pass@localhost/autocomplete"
```

### Tablas

| Tabla | Contenido |
|---|---|
| `words` | Palabras con peso, origen y timestamps |
| `history` | Historial de comandos ejecutados |
| `preferences` | Preferencias clave-valor en JSON |

### Backup y restore

```powershell
# Backup a la ruta por defecto (config_dir/backups/)
python -m autocomplete db backup

# Backup a ruta específica
python -m autocomplete db backup -o D:\backups\auto.db

# Restore
python -m autocomplete db restore .\backup.db --yes

# Compactar
python -m autocomplete db vacuum
```

Comportamiento por motor:

| Comando | SQLite | PostgreSQL | MySQL |
|---|---|---|---|
| `backup` | Copia el archivo `.db` | `pg_dump` | `mysqldump` |
| `restore` | Reemplaza el `.db` | `psql -f` | `mysql <` |
| `vacuum` | `VACUUM` | `VACUUM FULL` | `OPTIMIZE TABLE` |

### Resolución de `pg_dump` / `mysqldump`

Cuando el motor no es SQLite, `Storage.backup()` y `Storage.restore()`
buscan el ejecutable en este orden:

1. Variable de entorno `AUTOCOMPLETE_PG_DUMP` / `AUTOCOMPLETE_MYSQLDUMP`.
2. `shutil.which("pg_dump")` / `shutil.which("mysqldump")`.
3. Nombre pelado (`"pg_dump"` / `"mysqldump"`), que fallará si no está
   en el PATH.

Ejemplo con el `pg_dump` de pgAdmin que no está en el PATH:

```powershell
# Solo sesión actual
$env:AUTOCOMPLETE_PG_DUMP = "C:\Program Files\PostgreSQL\17\pgAdmin 4\runtime\pg_dump.exe"
python -m autocomplete db backup

# Permanente para el usuario
[Environment]::SetEnvironmentVariable(
    "AUTOCOMPLETE_PG_DUMP",
    "C:\Program Files\PostgreSQL\17\pgAdmin 4\runtime\pg_dump.exe",
    "User"
)
```

### Programático

```python
from autocomplete import Storage

with Storage("sqlite:///mi.db") as s:
    # Backup explícito a un directorio base
    path = s.backup(base_dir="/tmp/respaldos")

    # Backup a ruta exacta (ignora base_dir)
    path = s.backup("/tmp/respaldos/backup-manual.db")
```

---

## Daemon

Servidor TCP local que mantiene el Trie en memoria para que el Tab
responda sin levantar Python en cada pulsación.

- **Puerto**: guardado en `<config_dir>/daemon.port`.
- **PID**: guardado en `<config_dir>/daemon.pid`.
- **Protocolo**: JSON delimitado por salto de línea.

### Operaciones

`ping`, `suggest`, `correct`, `contains`, `stats`, `reload`, `shutdown`.

### Ciclo de vida

```powershell
python -m autocomplete daemon start
python -m autocomplete daemon status
python -m autocomplete daemon reload
python -m autocomplete daemon stop
```

### Sincronización automática

Cada vez que `db add`, `db remove`, `db restore` o `load-dir` se
ejecutan, el CLI avisa al daemon para que recargue desde la BD.

### Rendimiento

| Escenario | Latencia |
|---|---|
| CLI sin daemon | 150-300 ms |
| Daemon TCP | 5-15 ms |
| Librería embebida | <1 ms |

---

## Tab wrapper

### Instalación automática

```powershell
python -m autocomplete init
```

El asistente detecta el shell, instala el wrapper y lo añade al perfil.

### Instalación manual PowerShell

```powershell
python -m autocomplete install-ps
```

Añade la línea indicada a tu `$PROFILE`:

```powershell
. "$env:APPDATA\autocomplete\wrapper.ps1"
```

Recarga:

```powershell
. $PROFILE
```

### Instalación manual bash/zsh/fish

```bash
# bash
echo '[ -f "$HOME/.config/autocomplete/wrapper.bash" ] && source "$HOME/.config/autocomplete/wrapper.bash"' >> ~/.bashrc
source ~/.bashrc

# zsh
echo '[ -f "$HOME/.config/autocomplete/wrapper.zsh" ] && source "$HOME/.config/autocomplete/wrapper.zsh"' >> ~/.zshrc
source ~/.zshrc

# fish
echo 'source $HOME/.config/autocomplete/wrapper.fish' >> ~/.config/fish/config.fish
```

### Uso

```powershell
PS> git<TAB>          # completa con "git"
PS> <TAB>             # cicla: git-add → git-am → git-apply → ...
PS> git-<TAB>         # filtra por "git-"
PS> docker<TAB>       # → docker
```

El wrapper usa el daemon si está activo y cae al CLI si no lo está.

### Compatibilidad PSReadLine

El wrapper funciona en PSReadLine 2.0.0+ y 2.3.x. No intercepta la
tecla Enter (evita el error `No se encuentra el tipo
[Microsoft.PowerShell.PSReadLine]`). El estado del ciclo se resetea
automáticamente cuando el prefijo cambia.

Si PSReadLine no está cargado:

```powershell
Import-Module PSReadLine
```

Instalación si falta:

```powershell
Install-Module -Name PSReadLine -Scope CurrentUser -Force -AllowClobber
```

---

## Asistente `init`

Detecta el shell, crea la BD, carga palabras y arranca el daemon.

```powershell
python -m autocomplete init
```

Flujo interactivo:

1. Detecta shell (`pwsh`, `powershell`, `bash`, `zsh`, `fish`, `cmd`).
2. Pregunta si usar el shell detectado.
3. Muestra la configuración y permite cambiar la URL de BD.
4. Pregunta preferencias (`auto_execute`).
5. Ofrece cargar un archivo de palabras.
6. Instala el wrapper de Tab.
7. Arranca el daemon en background.

Modo no interactivo:

```powershell
python -m autocomplete init --yes
```

En modo no interactivo se usan los valores por defecto y se instala el
wrapper del shell detectado sin preguntar.

---

## Diccionario de comandos

### Archivo monolítico

`comandos.txt`: ~600 comandos en un solo archivo. Formato:

```text
# Comentario
git
git-commit
git-push
```

### Directorio por categorías

`comandos/` con 28 archivos `NN-categoria.txt`. Carga con:

```powershell
python -m autocomplete load-dir comandos --recursive --replace
```

Formato con pesos opcionales (TAB):

```text
git         10
git-commit   5
git-push     3
```

### Cargar a la BD

```powershell
# Un archivo
python -m autocomplete -f comandos.txt db init

# Directorio
python -m autocomplete load-dir comandos --recursive

# Palabras sueltas
python -m autocomplete db add git-fetch git-rebase --weight 5
```

---

## Integración en otros proyectos

### Como librería embebida

Ideal para scripts, generadores de documentos, procesamiento offline.

```python
from autocomplete import Autocomplete

ac = Autocomplete.from_file("comandos.txt")

def buscar(termino: str) -> list[str]:
    return ac.suggestions(termino, limit=5)
```

### Con Flask

```python
from flask import Flask, jsonify, request
from autocomplete import Autocomplete

app = Flask(__name__)
ac = Autocomplete.from_file("comandos.txt")

@app.get("/api/suggest")
def suggest():
    prefix = request.args.get("prefix", "")
    limit = int(request.args.get("limit", 10))
    return jsonify(suggestions=ac.suggestions(prefix, limit=limit))
```

### Con Django

```python
# views.py
from django.http import JsonResponse
from autocomplete import Autocomplete

_ac = Autocomplete.from_file("comandos.txt")

def suggest(request):
    prefix = request.GET.get("prefix", "")
    limit = int(request.GET.get("limit", 10))
    return JsonResponse({"suggestions": _ac.suggestions(prefix, limit=limit)})
```

### Como microservicio separado

Varias apps Python o de otros lenguajes pueden consumir un único
proceso que mantiene el Trie:

```text
[doc-generator]  ─┐
[blog]           ─┼──►  [servicio autocomplete]  ──►  [PostgreSQL]
[foro]           ─┘
```

El servicio expone los endpoints HTTP equivalentes a los subcomandos
del CLI. La forma más simple es montar un wrapper con FastAPI que
llame a `Autocomplete.suggestions` y `Autocomplete.correct` sobre una
instancia cargada desde `Storage`.

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY autocomplete ./autocomplete
RUN pip install --no-cache-dir ".[postgres]"
# Añade aquí tu wrapper HTTP (p. ej. uvicorn + FastAPI)
```

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: autocomplete
      POSTGRES_DB: autocomplete
    volumes: ["pgdata:/var/lib/postgresql/data"]

  api:
    build: .
    environment:
      AUTOCOMPLETE_DB_URL: postgresql+psycopg://postgres:autocomplete@db:5432/autocomplete
    depends_on: [db]

volumes: { pgdata: {} }
```

### Modos de integración recomendados

| Proyecto | Recomendación |
|---|---|
| Generador de documentos offline | Librería embebida |
| Blog/foro pequeño (1 worker) | Librería o Flask/Django directo |
| Blog/foro con varios workers | FastAPI + Redis/Postgres |
| Varias apps Python | Microservicio HTTP |
| Varias apps + otros lenguajes | Microservicio HTTP |
| Tab completion en consola | Daemon TCP |
| Editor de texto nativo | Daemon TCP |

---

## Tests

### Ejecutar

```powershell
pytest                              # todos
pytest -v                           # detallado
pytest tests/test_core.py           # un módulo
pytest tests/test_storage.py::TestCRUD   # una clase
pytest --cov=autocomplete --cov-report=term-missing
pytest --cov=autocomplete --cov-report=html
```

### Cobertura

La suite cubre:

- **`test_core.py`**: `Autocomplete` (sugerencias, add/remove,
  contains, correct, len, all_words) y `Trie`/`TrieNode`.
- **`test_similarity.py`**: `levenshtein`, `damerau_levenshtein`,
  `find_similar` (transposiciones, `max_dist`, orden, límite).
- **`test_text.py`**: `strip_accents` y `normalize_key` con casos
  vacíos, mayúsculas, caracteres no latinos y `remove_accents=False`.
- **`test_bulk_load.py`**: `bulk_load` desde `.txt`, `.tsv`, `.gz`,
  errores de formato, `on_progress`; `bulk_load_dir` con recursión,
  patrón, directorio inexistente.
- **`test_stats.py`**: `LoadStats` y `LoadDirStats` (conteos, errores
  agregados, `__str__`).
- **`test_storage.py`**: CRUD de palabras, historial, preferencias,
  `reset`, `backup`/`restore` SQLite, `vacuum`, backup mockeado de
  PostgreSQL y MySQL, motor desconocido, ciclo de vida con
  `close()` y context manager.
- **`test_config.py`**: defaults, `set`/`get`, persistencia JSON,
  `reset`, `db_url`, override por variables de entorno, archivo
  corrupto.
- **`test_execution.py`**: `run_command` con `capture=True/False`,
  timeout, `cwd`, éxito/fallo; `ExecutionResult.success`.
- **`test_server.py`**: `DaemonServer.dispatch` para todas las
  operaciones, cliente TCP end-to-end, lectura de `daemon.port`/
  `daemon.pid`, `status`, JSON inválido en el socket.
- **`test_cli.py`**: `build_parser`, `config`, `db` (todos los
  subcomandos), `suggest`, `correct`, `repl`, `shell`, `load-dir`,
  `daemon`, `install-ps`.
- **`test_wizard.py`**: `detect_shell`, `profile_path`,
  `_wrapper_text`, `_append_line_once`, mapeo de shells,
  `run_init(interactive=False)`.

### Reglas al añadir tests

- Cada funcionalidad nueva trae al menos un test.
- Cada bug corregido trae un test que lo reproduce.
- Usar `tmp_path` para archivos temporales.
- SQLite en memoria (`sqlite:///:memory:`) para tests de `Storage`
  siempre que no haya que verificar el archivo físico.
- Evitar depender de red, daemon real o estado del sistema.

---

## Solución de problemas

### `ModuleNotFoundError: No module named 'autocomplete'`

**Causa**: pytest no añade la raíz al `sys.path`.

**Solución**: en `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

O usar `python -m pytest` en vez de `pytest`.

### `ImportError: attempted relative import with no known parent package`

**Causa**: se ejecutó `python autocomplete` en lugar de
`python -m autocomplete`.

| Comando | Resultado |
|---|---|
| `python autocomplete` | ❌ imports relativos fallan |
| `python autocomplete\__main__.py` | ❌ igual |
| `python -m autocomplete` | ✅ correcto |
| `autocomplete` (instalado) | ✅ correcto |

**Solución**: usar `python -m autocomplete` o instalar con
`pip install -e .` y usar el comando `autocomplete`.

### `No se encuentra el tipo [Microsoft.PowerShell.PSReadLine]`

**Causa**: un wrapper antiguo intentaba usar
`[Microsoft.PowerShell.PSReadLine]::AcceptLine()`, un tipo que no
existe.

**Solución**: el wrapper actual no intercepta Enter. Si aparece el
error:

1. Reinstala el wrapper:
   ```powershell
   python -m autocomplete install-ps
   ```
2. Verifica la versión de PSReadLine:
   ```powershell
   Get-Module PSReadLine -ListAvailable | Select-Object Name, Version
   ```
3. Si es 2.0.0 y quieres actualizar:
   ```powershell
   Install-Module PSReadLine -Scope CurrentUser -Force -AllowClobber
   ```

### El daemon no arranca

```powershell
python -m autocomplete daemon status
python -m autocomplete daemon run      # primer plano para ver errores
python -m autocomplete daemon restart
```

### El Tab no responde o tarda mucho

1. Comprueba que el daemon esté activo:
   ```powershell
   python -m autocomplete daemon status
   ```
2. Si no lo está:
   ```powershell
   python -m autocomplete daemon start
   ```
3. Si sigue lento, revisa el tamaño de la BD: el daemon precarga todo
   el Trie al arrancar.

### `db backup` falla con PostgreSQL o MySQL

El ejecutable no está en el PATH. Apunta a él con la variable de
entorno:

```powershell
$env:AUTOCOMPLETE_PG_DUMP = "C:\ruta\a\pg_dump.exe"
$env:AUTOCOMPLETE_MYSQLDUMP = "C:\ruta\a\mysqldump.exe"
```

### `database is locked` (SQLite)

Solo ocurre si dos procesos escriben a la vez. El daemon solo lee; el
CLI escribe. Si persiste:

```powershell
python -m autocomplete db vacuum
```

---

## Licencia

MIT. Consulta `LICENSE`.