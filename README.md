# autocomplete

Módulo reutilizable de autocompletado, autocorrección y sugerencia de
comandos basado en Trie. Incluye CLI, daemon, Tab wrapper, persistencia
con SQLAlchemy, API HTTP opcional y soporte para integración como
librería embebida.

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
13. [API HTTP (FastAPI)](#api-http-fastapi)
14. [Integración en otros proyectos](#integración-en-otros-proyectos)
15. [Tests](#tests)
16. [Solución de problemas](#solución-de-problemas)
17. [Historial de cambios](#historial-de-cambios)
18. [Licencia](#licencia)

---

## Descripción

`autocomplete` es un paquete Python que ofrece:

- **Autocompletado por prefijo** (Trie con pesos/frecuencia).
- **Autocorrección** de typos (distancia Damerau-Levenshtein).
- **Normalización de acentos** (`"cafe"` encuentra `"café"`).
- **Carga masiva** desde `.txt`, `.tsv`, `.gz` y directorios completos.
- **Persistencia** con SQLAlchemy (SQLite por defecto, PostgreSQL/MySQL
  cambiando solo la URL).
- **CLI** con subcomandos.
- **Daemon TCP local** para que el Tab responda en ~5-15 ms.
- **Tab wrapper** para PowerShell, bash, zsh y fish.
- **API HTTP** opcional con FastAPI para integración web.

---

## Requerimientos

### Software

- **Python 3.9+** (probado en 3.13).
- **SQLAlchemy 2.0+**.
- **PowerShell 5.1+** o **PowerShell 7+** (para el wrapper de Windows).
- **PSReadLine 2.0+** (viene con Windows PowerShell 5.1 y PowerShell 7).

### Opcional

- `psycopg[binary]>=3.1` para PostgreSQL.
- `pymysql>=1.1` para MySQL/MariaDB.
- `fastapi[standard]` + `uvicorn` para el API HTTP.
- `pytest>=7` para tests.

### Herramientas del sistema (solo si usas backup/restore)

- SQLite: ninguna (copia directa del archivo).
- PostgreSQL: `pg_dump` y `psql` en el PATH.
- MySQL/MariaDB: `mysqldump` y `mysql` en el PATH.

### Sistema operativo

- **Windows** (wrapper PowerShell `.ps1`).
- **Linux / macOS** (wrappers bash/zsh/fish).

---

## Instalación

### 1. Clonar o crear el proyecto

```powershell
mkdir D:\Programacion\Proyectos\Autocompletado
cd D:\Programacion\Proyectos\Autocompletado
```

### 2. Crear el entorno virtual (recomendado)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar en modo editable

```powershell
pip install -e .
```

Con dependencias opcionales:

```powershell
pip install -e ".[dev,postgres]"
```

### 4. Verificar

```powershell
python -m autocomplete -h
```

Debe mostrar la ayuda del CLI.

> ⚠️ **Importante**: usar `python -m autocomplete`, **no** `python autocomplete`.
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
├── comandos.txt                    # diccionario monolítico (opcional)
├── comandos/                       # diccionario por categorías
│   ├── 01-git.txt
│   ├── 02-docker.txt
│   ├── 03-kubernetes.txt
│   ├── ... (28 archivos)
│   └── 28-devops.txt
├── autocomplete/                   # paquete principal
│   ├── __init__.py                 # API pública (re-exports)
│   ├── __main__.py                 # entry point `python -m autocomplete`
│   ├── py.typed                    # marcador PEP 561 (type hints)
│   ├── exceptions.py               # excepciones transversales
│   │
│   ├── core/                       # dominio: lógica pura, sin I/O
│   │   ├── __init__.py
│   │   ├── engine.py               # clase Autocomplete
│   │   ├── trie.py                 # Trie + TrieNode
│   │   ├── similarity.py           # Levenshtein / Damerau
│   │   └── stats.py                # LoadStats / LoadDirStats
│   │
│   ├── text/                       # utilidades de texto
│   │   ├── __init__.py
│   │   └── normalization.py        # strip_accents, normalize_key
│   │
│   ├── storage/                    # persistencia
│   │   ├── __init__.py
│   │   ├── models.py               # Base + WordRecord / HistoryRecord / PreferenceRecord
│   │   ├── repository.py           # Storage (CRUD)
│   │   └── maintenance.py          # backup, restore, vacuum, reset
│   │
│   ├── config/                     # configuración
│   │   ├── __init__.py
│   │   └── settings.py             # Config + rutas por SO
│   │
│   ├── server/                     # daemon y cliente TCP
│   │   ├── __init__.py
│   │   ├── protocol.py             # constantes del protocolo JSON
│   │   ├── daemon.py               # servidor TCP
│   │   └── client.py               # cliente con fallback
│   │
│   ├── execution/                  # ejecución de comandos
│   │   ├── __init__.py
│   │   └── runner.py               # run_command, ExecutionResult
│   │
│   ├── interfaces/                 # puntos de entrada
│   │   ├── __init__.py
│   │   ├── cli.py                  # CLI argparse
│   │   ├── api.py                  # API HTTP (FastAPI) opcional
│   │   └── wizard.py               # asistente `init`
│   │
│   └── assets/                     # recursos empaquetados
│       ├── wrapper.ps1             # Tab wrapper PowerShell
│       ├── wrapper.bash            # Tab wrapper bash
│       ├── wrapper.zsh             # Tab wrapper zsh
│       └── wrapper.fish            # Tab wrapper fish
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_core.py
    ├── test_similarity.py
    ├── test_storage.py
    ├── test_config.py
    └── test_cli.py
```

### Reglas de dependencia entre capas

Cada capa puede importar de las inferiores, pero nunca al revés. Esto
garantiza que `core` sea testeable sin base de datos ni red.

```text
interfaces  →  server / execution / storage / config
                ↓
              core  ←  text
                ↓
           exceptions
```

| Capa | Responsabilidad | Puede importar de |
|---|---|---|
| `interfaces` | Puntos de entrada (CLI, HTTP, wizard) | Todo lo demás |
| `server` | Daemon TCP y cliente | `core`, `storage`, `config` |
| `execution` | Ejecución de comandos | `exceptions` |
| `storage` | Persistencia SQLAlchemy | `config`, `exceptions` |
| `config` | Configuración JSON | `exceptions` |
| `core` | Lógica pura del Trie y motor | `text`, `exceptions` |
| `text` | Normalización de texto | `exceptions` |
| `exceptions` | Excepciones | — (nada) |

### Mapa de módulos

| Archivo | Responsabilidad |
|---|---|
| `core/engine.py` | Clase `Autocomplete` con métodos públicos |
| `core/trie.py` | Estructura de datos `Trie` / `TrieNode` |
| `core/similarity.py` | `levenshtein`, `damerau_levenshtein`, `find_similar` |
| `core/stats.py` | `LoadStats`, `LoadDirStats` |
| `text/normalization.py` | `strip_accents`, `normalize_key` |
| `storage/models.py` | Modelos ORM (`WordRecord`, etc.) |
| `storage/repository.py` | Clase `Storage` con CRUD |
| `storage/maintenance.py` | `backup`, `restore`, `vacuum`, `reset` |
| `config/settings.py` | Clase `Config`, rutas por SO |
| `server/daemon.py` | Servidor TCP que mantiene el Trie en memoria |
| `server/client.py` | Cliente con fallback silencioso al CLI |
| `server/protocol.py` | Constantes y helpers del protocolo JSON |
| `execution/runner.py` | `run_command`, `ExecutionResult` |
| `interfaces/cli.py` | Parser argparse + handlers |
| `interfaces/api.py` | Endpoints FastAPI |
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
    Autocomplete,       # clase principal
    LoadStats,          # stats de bulk_load
    LoadDirStats,       # stats de bulk_load_dir
    Config,             # configuración persistente
    Storage,            # persistencia SQLAlchemy
    ExecutionResult,    # resultado de run_command
    run_command,        # ejecutor de comandos
    strip_accents,      # util de normalización
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

Ejecutable con `python -m autocomplete` o `autocomplete` (si está instalado).

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
--separator SEP         Separador de columnas (\t, ,, etc.)
--db-url URL            URL SQLAlchemy
--no-db                 No usar BD
--no-accents            Desactiva normalización de acentos
```

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
```

### Subcomandos `db`

| Comando | Descripción |
|---|---|
| `db init` | Inicializa la BD |
| `db info` | Muestra información |
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

---

## Base de datos

### Motor por defecto: SQLite

Se crea en `<config_dir>/data.db` automáticamente.

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
# Backup
python -m autocomplete db backup
python -m autocomplete db backup -o D:\backups\auto.db

# Restore
python -m autocomplete db restore .\backup.db --yes

# Compactar
python -m autocomplete db vacuum
```

Comportamiento por motor:

| Comando | SQLite | PostgreSQL | MySQL |
|---|---|---|---|
| `backup` | Copia `.db` | `pg_dump` | `mysqldump` |
| `restore` | Copia sobre `.db` | `psql -f` | `mysql <` |
| `vacuum` | `VACUUM` | `VACUUM FULL` | `OPTIMIZE TABLE` |

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

El asistente detecta el shell, instala el wrapper y configura el perfil.

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

El wrapper funciona en PSReadLine 2.0.0+ y 2.3.x. **No intercepta la
tecla Enter** (evita el error `No se encuentra el tipo
[Microsoft.PowerShell.PSReadLine]`). El estado del ciclo se resetea
automáticamente cuando cambia el prefijo.

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
3. Muestra configuración y permite cambiar la URL de BD.
4. Pregunta preferencias (auto_execute).
5. Ofrece cargar un archivo de palabras.
6. Instala el wrapper de Tab.
7. Arranca el daemon en background.

Modo no interactivo:

```powershell
python -m autocomplete init --yes
```

---

## Diccionario de comandos

### Archivo monolítico

`comandos.txt`: ~600 líneas con comandos de Git, Docker, Kubernetes,
AWS, Azure, GCloud, Python, Node, Java, Go, Rust, Ruby, PHP, .NET,
PowerShell, CMD, Linux coreutils, redes, bases de datos, package
managers, servidores web, editores, multimedia y DevOps.

### Directorio por categorías

`comandos/` con 28 archivos `NN-categoria.txt`. Carga con:

```powershell
python -m autocomplete load-dir comandos --recursive --replace
```

Formato:

```text
# Comentario
git
git-commit
git-push
```

O con pesos (separador TAB):

```text
git         10
git-commit   5
git-push     3
```

### Añadir a la BD

```powershell
# Un archivo
python -m autocomplete -f comandos.txt db init

# Directorio
python -m autocomplete load-dir comandos --recursive

# Palabras sueltas
python -m autocomplete db add git-fetch git-rebase --weight 5
```

---

## API HTTP (FastAPI)

### Instalación

```powershell
pip install "fastapi[standard]" uvicorn
```

### Arranque

```powershell
uvicorn autocomplete.api:app --host 127.0.0.1 --port 8765
```

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado + número de palabras |
| GET | `/suggest?prefix=X&limit=N` | Sugerencias |
| GET | `/correct?word=X&max_distance=N&limit=N` | Correcciones |
| GET | `/contains?word=X` | ¿Existe? |
| POST | `/words` | Añade palabras |
| POST | `/reload` | Recarga desde la BD |

### Ejemplo

```powershell
curl "http://127.0.0.1:8765/suggest?prefix=git&limit=5"
```

```json
{
  "prefix": "git",
  "suggestions": ["git", "git-add", "git-am", "git-apply", "git-archive"]
}
```

### Frontend JavaScript

```javascript
const input = document.getElementById('buscar');

input.addEventListener('input', async (e) => {
  const q = e.target.value.trim();
  if (!q) return;

  const r = await fetch(
    `http://127.0.0.1:8765/suggest?prefix=${encodeURIComponent(q)}&limit=10`
  );
  const data = await r.json();
  console.log(data.suggestions);
});
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

```
[doc-generator]  ─┐
[blog]           ─┼──►  [autocomplete-api :8765]  ──►  [PostgreSQL]
[foro]           ─┘
```

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY autocomplete ./autocomplete
RUN pip install --no-cache-dir ".[postgres]" "fastapi[standard]" uvicorn
EXPOSE 8765
CMD ["uvicorn", "autocomplete.api:app", "--host", "0.0.0.0", "--port", "8765"]
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
    ports: ["8765:8765"]
    depends_on: [db]

volumes: { pgdata: {} }
```

### Modos de integración recomendados

| Proyecto | Recomendación |
|---|---|
| Generador de documentos offline | Librería embebida |
| Blog/foro pequeño (1 worker) | Librería o Flask/Django directo |
| Blog/foro con varios workers | FastAPI + Redis/Postgres |
| Varias apps Python | FastAPI microservicio |
| Varias apps + otros lenguajes | FastAPI microservicio |
| Tab completion en consola | Daemon TCP |
| Editor de texto nativo | Daemon TCP |

---

## Tests

```powershell
pytest
pytest -v
pytest --cov=autocomplete
```

Cobertura de los tests:

- Sugerencias básicas y con límite.
- Orden por frecuencia y alfabético.
- Acentos (normalización, `remove_accents=False`).
- `add_word`, `add_words`, `remove_word`, `contains`, `__len__`.
- `bulk_load` desde `.txt`, `.tsv`, `.gz`.
- Errores de formato y progreso.
- `bulk_load_dir` (directorio).

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

O usa `python -m pytest` en vez de `pytest`.

### `ImportError: attempted relative import with no known parent package`

**Causa**: ejecutaste `python autocomplete` en vez de `python -m autocomplete`.

**Explicación**:

| Comando | Resultado |
|---|---|
| `python autocomplete` | ❌ imports relativos fallan |
| `python autocomplete\__main__.py` | ❌ igual |
| `python -m autocomplete` | ✅ correcto |
| `autocomplete` (instalado) | ✅ correcto |

**Solución**: usa `python -m autocomplete` o instala con `pip install -e .`
y usa el comando `autocomplete` directamente.

### `No se encuentra el tipo [Microsoft.PowerShell.PSReadLine]`

**Causa**: el wrapper intentaba usar `[Microsoft.PowerShell.PSReadLine]::AcceptLine()`, un tipo que no existe.

**Solución**: el wrapper actual **no intercepta Enter**. El estado del
ciclo de Tab se resetea cuando cambia el prefijo. Si el error aparece:

1. Actualiza el wrapper:
   ```powershell
   python -m autocomplete install-ps
   ```
2. Verifica la versión de PSReadLine:
   ```powershell
   Get-Module PSReadLine -ListAvailable | Select-Object Name, Version
   ```
3. Si es 2.0.0, actualiza:
   ```powershell
   Install-Module PSReadLine -Scope CurrentUser -Force -AllowClobber
   ```

### El daemon no arranca

```powershell
# Ver estado
python -m autocomplete daemon status

# Intentar arranque manual para ver errores
python -m autocomplete daemon run

# Forzar reinicio
python -m autocomplete daemon restart
```

### El Tab no responde o tarda mucho

1. Verifica que el daemon esté activo:
   ```powershell
   python -m autocomplete daemon status
   ```
2. Si no está activo, arráncalo:
   ```powershell
   python -m autocomplete daemon start
   ```
3. Si sigue lento, revisa que la BD no sea enorme. El daemon precarga todo el Trie al arrancar.

### Backup falla en PostgreSQL

```powershell
# Verificar que pg_dump esté en PATH
Get-Command pg_dump
```

Si no está, añade `C:\Program Files\PostgreSQL\<version>\bin` al PATH.

### `database is locked` (SQLite)

Solo ocurre si abres la BD desde dos procesos que escriben. El daemon
solo lee; el CLI escribe. Si persiste:

```powershell
python -m autocomplete db vacuum
```

---

## Historial de cambios

### v1.5.0

- `db restore` y `db vacuum`.
- `db history --clear`.
- `db info` con tamaño de BD.
- Detección de motor (SQLite/Postgres/MySQL) en `Storage`.
- `_sqlite_path()` para manejo correcto de rutas Windows.

### v1.4.0

- Daemon TCP local.
- Cliente con fallback al CLI.
- Asistente `autocomplete init`.
- Wrappers `.ps1/.bash/.zsh/.fish` daemon-aware.

### v1.3.0

- Persistencia con SQLAlchemy.
- Historial de comandos.
- Preferencias en tabla + JSON.

### v1.2.0

- CLI con subcomandos (`suggest`, `correct`, `shell`, `repl`).
- Autocorrección con Damerau-Levenshtein.
- Modo `shell` con ejecución de comandos.

### v1.1.0

- Normalización de acentos con `unicodedata`.
- `bulk_load` desde archivos.
- `LoadStats`.

### v1.0.0

- Versión inicial con `Autocomplete` y `Trie`.

---

## Licencia

MIT. Consulta `LICENSE` si lo incluyes.