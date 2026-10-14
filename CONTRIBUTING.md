# Contribuir a autocomplete

Gracias por tu interés en contribuir. Este documento describe el flujo
de trabajo, las convenciones y cómo preparar el entorno.

---

## Tabla de contenidos

1. [Código de conducta](#código-de-conducta)
2. [Requerimientos del entorno](#requerimientos-del-entorno)
3. [Configuración inicial](#configuración-inicial)
4. [Flujo de trabajo](#flujo-de-trabajo)
5. [Convenciones de commits](#convenciones-de-commits)
6. [Convenciones de código](#convenciones-de-código)
7. [Tests](#tests)
8. [Estructura del proyecto](#estructura-del-proyecto)
9. [Cómo añadir una funcionalidad](#cómo-añadir-una-funcionalidad)
10. [Cómo reportar un bug](#cómo-reportar-un-bug)
11. [Cómo proponer una mejora](#cómo-proponer-una-mejora)
12. [Pull requests](#pull-requests)
13. [Checklist antes de enviar un PR](#checklist-antes-de-enviar-un-pr)

---

## Código de conducta

- Sé respetuoso en issues, PRs y discusiones.
- Crítica al código, no a la persona.
- Si algo no está claro, pregunta antes de asumir.
- No se aceptan contribuciones que rompan compatibilidad sin discusión
  previa en un issue.

---

## Requerimientos del entorno

### Software base

- Python 3.9+
- Git
- PowerShell 7+ (opcional, solo para el wrapper de Windows)

### Herramientas del sistema (solo si tocas backup/restore)

- PostgreSQL: `pg_dump`, `psql`
- MySQL/MariaDB: `mysqldump`, `mysql`

No es obligatorio tenerlas en el PATH: se pueden apuntar con
`AUTOCOMPLETE_PG_DUMP` y `AUTOCOMPLETE_MYSQLDUMP`.

### Dependencias del proyecto

Se instalan con `pip install -e ".[dev]"`.

---

## Configuración inicial

### 1. Fork y clon

```powershell
git clone https://github.com/bryangarcia1204/Autocompletado.git
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

### 3. Instalar en modo editable con extras de desarrollo

```powershell
pip install -e ".[dev,postgres]"
```

### 4. Verificar que todo arranca

```powershell
python -m autocomplete -h
pytest
```

Si `pytest` falla con `ModuleNotFoundError`, comprueba que en
`pyproject.toml` esté:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

### 5. Configurar el remoto

```powershell
git remote add upstream https://github.com/bryangarcia1204/Autocompletado.git
git fetch upstream
```

---

## Flujo de trabajo

1. **Actualiza `main`**:

   ```powershell
   git checkout main
   git pull upstream main
   ```

2. **Crea una rama descriptiva**:

   ```powershell
   git checkout -b feat/daemon-autostart
   # o
   git checkout -b fix/tab-wrapper-psreadline
   ```

3. **Trabaja en pasos pequeños**. Commitea con frecuencia.

4. **Corre los tests**:

   ```powershell
   pytest
   ```

5. **Aplica formato y lint** (ver [Convenciones de código](#convenciones-de-código)).

6. **Push a tu fork**:

   ```powershell
   git push origin feat/daemon-autostart
   ```

7. **Abre un Pull Request** contra `upstream/main`.

### Nombres de rama

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Funcionalidad | `feat/` | `feat/daemon-autostart` |
| Corrección | `fix/` | `fix/tab-psreadline` |
| Documentación | `docs/` | `docs/readme-instalacion` |
| Refactor | `refactor/` | `refactor/cli-argparse` |
| Tests | `test/` | `test/bulk-load-gz` |
| Mantenimiento | `chore/` | `chore/bump-version` |

---

## Convenciones de commits

Se sigue **Conventional Commits**.

### Formato

```text
<tipo>(<alcance opcional>): <descripción corta>

<cuerpo opcional>

<footer opcional>
```

### Tipos permitidos

| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `style` | Formato, espacios (sin cambio funcional) |
| `refactor` | Refactor sin cambio funcional |
| `perf` | Mejora de rendimiento |
| `test` | Añadir o corregir tests |
| `chore` | Tareas de mantenimiento |
| `build` | Cambios en `pyproject.toml`, CI |

### Ejemplos

```text
feat(daemon): añade autostart en primer Tab
fix(wrapper): elimina handler Enter incompatible con PSReadLine 2.0
docs(readme): documenta integración con Flask
test(bulk_load): cubre archivos .gz comprimidos
refactor(storage): extrae _sqlite_path()
```

### Reglas

- Descripción en **imperativo** ("añade", no "añadido").
- Máximo 72 caracteres en la primera línea.
- Sin punto final en la primera línea.
- Cuerpo solo si hace falta explicar el "por qué", no el "qué".

---

## Convenciones de código

### Estilo general

- **PEP 8**.
- **Type hints** en todas las funciones y métodos públicos.
- **Docstrings** en formato Google o reStructuredText, en español.
- **Longitud máxima de línea**: 88 caracteres (compatible con Black).
- **Sin prints** en librería; usar `logging` o devolver valores.
- **Sin dependencias nuevas** sin discusión previa en un issue.

### Herramientas

```powershell
black autocomplete tests
isort autocomplete tests
ruff check autocomplete tests
mypy autocomplete
pytest --cov=autocomplete
```

### Ejemplo de función bien formada

```python
def suggestions(
    self,
    prefix: str,
    limit: Optional[int] = None,
    sort_by_frequency: bool = True,
) -> List[str]:
    """Devuelve las sugerencias que comienzan con ``prefix``.

    Args:
        prefix: Prefijo a buscar.
        limit: Número máximo de sugerencias. ``None`` = sin límite.
        sort_by_frequency: Si ``True``, ordena por frecuencia descendente
            y desempata alfabéticamente.

    Returns:
        Lista de palabras sugeridas.

    Raises:
        InvalidPrefixError: Si ``prefix`` no es un ``str``.
    """
    ...
```

### Reglas específicas del proyecto

- Métodos públicos empiezan por verbo (`add_`, `remove_`, `get_`,
  `bulk_`, `find_`, `load_`).
- Métodos privados llevan prefijo `_`.
- No romper la API pública sin actualizar `autocomplete/__init__.py`,
  `__all__` y la versión.
- Los mensajes de error van en español y son accionables.
- Los imports dentro de un subpaquete usan `.` (mismo nivel) o `..`
  (nivel superior). Nunca absolutos dentro del paquete.
- Los imports entre capas respetan el orden de dependencias (ver
  [Estructura del proyecto](#estructura-del-proyecto)).

---

## Tests

### Ejecutar

```powershell
pytest                                              # todos
pytest -v                                           # detallado
pytest tests/test_core.py                           # un módulo
pytest tests/test_storage.py::TestCRUD              # una clase
pytest -k "acentos"                                 # por patrón
pytest --cov=autocomplete --cov-report=term-missing
pytest --cov=autocomplete --cov-report=html
```

### Reglas

- Cada funcionalidad nueva **debe** traer al menos un test.
- Cada bug corregido **debe** traer un test que lo reproduzca.
- Usar `tmp_path` para archivos temporales.
- SQLite en memoria (`sqlite:///:memory:`) para tests de `Storage`
  siempre que no haya que verificar el archivo físico.
- Evitar depender de red, daemon real o estado del sistema.
- Los tests que necesiten aislar la configuración del usuario usan
  `monkeypatch.setenv("AUTOCOMPLETE_CONFIG", ...)`.

### Estructura de un test

```python
def test_sugerencias_basicas(ac_basico: Autocomplete) -> None:
    assert ac_basico.suggestions("cas") == [
        "casa",
        "casamiento",
        "casco",
    ]
```

Nombres descriptivos en español, sin abreviaturas.

### Módulos de test

| Archivo | Cubre |
|---|---|
| `test_core.py` | `Autocomplete`, `Trie`, `TrieNode` |
| `test_similarity.py` | `levenshtein`, `damerau_levenshtein`, `find_similar` |
| `test_text.py` | `strip_accents`, `normalize_key` |
| `test_stats.py` | `LoadStats`, `LoadDirStats` |
| `test_bulk_load.py` | `bulk_load`, `bulk_load_dir` |
| `test_storage.py` | `Storage` (CRUD, historial, preferencias, backup, restore, vacuum) |
| `test_config.py` | `Config` y rutas por SO |
| `test_execution.py` | `run_command`, `ExecutionResult` |
| `test_server.py` | `DaemonServer`, `DaemonClient`, estado en disco |
| `test_cli.py` | Parser y handlers del CLI |
| `test_wizard.py` | Asistente `init` |

---

## Estructura del proyecto

```text
autocomplete/
├── __init__.py                 # API pública (re-exports)
├── __main__.py                 # entry point `python -m autocomplete`
├── py.typed                    # marcador PEP 561
├── exceptions.py
├── core/
│   ├── __init__.py
│   ├── engine.py
│   ├── trie.py
│   ├── similarity.py
│   └── stats.py
├── text/
│   ├── __init__.py
│   └── normalization.py
├── storage/
│   ├── __init__.py
│   ├── models.py
│   └── repository.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── server/
│   ├── __init__.py
│   ├── daemon.py
│   └── client.py
├── execution/
│   ├── __init__.py
│   └── runner.py
├── interfaces/
│   ├── __init__.py
│   ├── cli.py
│   └── wizard.py
└── assets/
    ├── __init__.py
    ├── wrapper.ps1
    ├── wrapper.bash
    ├── wrapper.zsh
    └── wrapper.fish
```

### Mapa de módulos

| Archivo | Responsabilidad |
|---|---|
| `core/engine.py` | Clase `Autocomplete` |
| `core/trie.py` | `Trie`, `TrieNode` |
| `core/similarity.py` | `levenshtein`, `damerau_levenshtein`, `find_similar` |
| `core/stats.py` | `LoadStats`, `LoadDirStats` |
| `text/normalization.py` | `strip_accents`, `normalize_key` |
| `storage/models.py` | Modelos ORM |
| `storage/repository.py` | Clase `Storage` (CRUD, backup, restore, vacuum, reset) |
| `config/settings.py` | Clase `Config`, rutas por SO |
| `server/daemon.py` | Servidor TCP |
| `server/client.py` | Cliente con fallback |
| `execution/runner.py` | `run_command`, `ExecutionResult` |
| `interfaces/cli.py` | Parser argparse y handlers |
| `interfaces/wizard.py` | Asistente `autocomplete init` |

### Reglas de dependencia

```text
interfaces  →  server / execution / storage / config
                ↓
              core  ←  text
                ↓
           exceptions
```

Cada capa solo importa de las inferiores. `core` nunca importa de
`storage`, `server` ni `interfaces`.

---

## Cómo añadir una funcionalidad

Ejemplo: añadir un subcomando `autocomplete stats`.

1. **Abre un issue** describiendo la funcionalidad y el caso de uso.

2. **Crea la rama**:

   ```powershell
   git checkout -b feat/command-stats
   ```

3. **Implementa la lógica** en la capa correspondiente:

   - Si es consulta de BD, en `storage/repository.py`.
   - Si es cálculo puro, en `core/`.
   - Si es orquestación, en `interfaces/cli.py`.

4. **Expón el comando** en `interfaces/cli.py`:

   - Añade el subparser en `build_parser()`.
   - Añade el handler correspondiente.
   - Engánchalo en `main()`.

5. **Añade tests** en el archivo correspondiente de `tests/`
   (`test_cli.py` si es un subcomando, `test_storage.py` si es
   persistencia, etc.).

6. **Actualiza `README.md`** con la nueva sección si es un comando.

7. **Actualiza `CHANGELOG.md`** bajo `## [Unreleased]`.

8. **Sube la versión** en `pyproject.toml` y `autocomplete/__init__.py`
   siguiendo SemVer.

9. **Commit y PR**.

---

## Cómo reportar un bug

Incluye:

- **Versión de Python** (`python --version`).
- **Sistema operativo** y versión.
- **Versión del paquete** (`pip show brayan-autocomplete`).
- **Pasos para reproducir** (lo más concretos posible).
- **Comportamiento esperado** vs **observado**.
- **Traza completa** si hay error.
- **Configuración relevante** (`python -m autocomplete config show`,
  omitiendo datos sensibles).

### Ejemplo

```text
Versión de Python: 3.13.7
SO: Windows 11
Versión del paquete: 1.0.0

Pasos:
1. Ejecuto `python -m autocomplete shell --yes`
2. Escribo `gti status`
3. El comando se ejecuta pero no se guarda en historial

Esperado: aparecer en `db history`
Observado: la tabla sigue vacía

Traza: (ninguna, no lanza excepción)

Config: auto_execute=true, database_url=sqlite:///...
```

---

## Cómo proponer una mejora

Abre un issue con la etiqueta `enhancement` y describe:

- **Problema** que resuelve.
- **Propuesta** concreta (API, comando, cambio de comportamiento).
- **Alternativas** consideradas.
- **Impacto** en compatibilidad.

Si el cambio es grande, espera aprobación antes de empezar a codificar.

---

## Pull requests

### Título

Sigue el formato de los commits:

```text
feat(daemon): añade autostart en primer Tab
```

### Descripción

Incluye:

- **Qué** cambia.
- **Por qué**.
- **Cómo probarlo** (comandos concretos).
- **Referencias** a issues (`Closes #42`).

### Revisión

- Un PR requiere al menos una aprobación.
- El CI debe pasar (tests + lint).
- Los comentarios de revisión se resuelven antes del merge.

### Merge

- **Squash and merge** para PRs pequeños.
- Merge normal para PRs grandes.
- La rama se borra después.

---

## Checklist antes de enviar un PR

- [ ] Rama basada en `main` actualizado.
- [ ] Nombre de rama descriptivo.
- [ ] Commits con Conventional Commits.
- [ ] Tests añadidos o actualizados.
- [ ] `pytest` pasa en local.
- [ ] `black`, `isort`, `ruff` y `mypy` sin errores.
- [ ] Docstrings actualizados.
- [ ] `README.md` actualizado si aplica.
- [ ] `CHANGELOG.md` actualizado bajo `[Unreleased]`.
- [ ] Versión subida si aplica (SemVer).
- [ ] Sin cambios no relacionados en el PR.
- [ ] Sin archivos temporales ni `.pyc` commiteados.

---

Gracias por contribuir.