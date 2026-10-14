# Contribuir a autocomplete

Gracias por tu interés en contribuir. Este documento describe el flujo de
trabajo, las convenciones y cómo preparar el entorno.

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
9. [Cómo añadir una nueva funcionalidad](#cómo-añadir-una-nueva-funcionalidad)
10. [Cómo reportar un bug](#cómo-reportar-un-bug)
11. [Cómo proponer una mejora](#cómo-proponer-una-mejora)
12. [Pull requests](#pull-requests)
13. [Checklist antes de enviar un PR](#checklist-antes-de-enviar-un-pr)

---

## Código de conducta

- Sé respetuoso en issues, PRs y discusiones.
- Crítica al código, no a la persona.
- Si algo no está claro, pregunta antes de asumir.
- No se aceptan contribuciones que rompan compatibilidad sin discusión previa.

---

## Requerimientos del entorno

### Software

- Python 3.9+
- Git
- PowerShell 7+ (opcional, solo para el wrapper de Windows)

### Herramientas del sistema (solo si tocas backup/restore)

- `pg_dump`, `psql` (PostgreSQL)
- `mysqldump`, `mysql` (MySQL/MariaDB)

### Dependencias del proyecto

Se instalan solas con `pip install -e ".[dev]"`.

---

## Configuración inicial

### 1. Fork y clon

```powershell
git clone https://github.com/<tu-usuario>/autocomplete.git
cd autocomplete
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

Si `pytest` falla con `ModuleNotFoundError`, revisa que en `pyproject.toml`
esté:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

### 5. Configurar el remoto

```powershell
git remote add upstream https://github.com/<org>/autocomplete.git
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

```
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

```
feat(daemon): añade autostart en primer Tab
fix(wrapper): elimina handler Enter incompatible con PSReadLine 2.0
docs(readme): documenta integración con FastAPI
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

- **PEP 8** estricto.
- **Type hints** en todas las funciones y métodos públicos.
- **Docstrings** en formato Google o reStructuredText, en inglés o español.
  El código actual está en español para docstrings, así que se mantiene.
- **Longitud máxima de línea**: 88 caracteres (compatible con Black).
- **Sin prints** en librería; usar `logging` o devolver valores.
- **Sin dependencias nuevas** sin discusión previa en un issue.

### Herramientas recomendadas

```powershell
# Formato
black autocomplete tests

# Orden de imports
isort autocomplete tests

# Lint
ruff check autocomplete tests

# Tipos
mypy autocomplete

# Tests
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

- Los nombres de archivos y clases en **español** cuando describen lógica
  de negocio; en **inglés** para utilidades técnicas.
- Los métodos públicos empiezan por verbo (`add_`, `remove_`, `get_`,
  `bulk_`, `find_`).
- Los privados llevan prefijo `_`.
- No romper la API pública sin actualizar `__init__.py`, `__all__` y
  la versión.
- Los mensajes de error van en español y son accionables.

---

## Tests

### Ejecutar

```powershell
pytest                     # todos
pytest tests/test_autocomplete.py
pytest -v
pytest -k "acentos"
pytest --cov=autocomplete --cov-report=html
```

### Reglas

- Cada funcionalidad nueva **debe** traer al menos un test.
- Cada bug corregido **debe** traer un test que lo reproduzca.
- Usar `tmp_path` para archivos temporales.
- No mockear la BD si se puede usar SQLite en memoria (`sqlite:///:memory:`).
- Evitar depender de red o de estado externo.

### Estructura de un test

```python
def test_sugerencias_basicas(ac: Autocomplete) -> None:
    assert ac.suggestions("cas") == ["casa", "casamiento", "casco"]
```

Nombres descriptivos en español, sin abreviaturas raras.

---

## Estructura del proyecto

| Archivo | Responsabilidad |
|---|---|
| `autocomplete.py` | Clase `Autocomplete` y `LoadStats` |
| `trie.py` | Estructura de datos Trie |
| `similarity.py` | Levenshtein y Damerau-Levenshtein |
| `text_utils.py` | Normalización de texto |
| `storage.py` | Persistencia SQLAlchemy |
| `config.py` | Configuración JSON |
| `executor.py` | Ejecución de comandos |
| `cli.py` | Interfaz argparse |
| `daemon.py` | Servidor TCP |
| `client.py` | Cliente del daemon |
| `init_wizard.py` | Asistente `init` |
| `api.py` | API HTTP (FastAPI) |
| `exceptions.py` | Excepciones |
| `__main__.py` | Entry point `python -m autocomplete` |

---

## Cómo añadir una nueva funcionalidad

Ejemplo: añadir un comando `autocomplete stats`.

1. **Abre un issue** describiendo la funcionalidad y el caso de uso.

2. **Crea la rama**:
   ```powershell
   git checkout -b feat/command-stats
   ```

3. **Implementa la lógica** en el módulo correspondiente (por ejemplo,
   `storage.py` si es consulta de BD).

4. **Expón el comando** en `cli.py`:
   - Añade el subparser en `build_parser()`.
   - Añade el handler.
   - Engánchalo en `main()`.

5. **Añade tests** en `tests/test_autocomplete.py` o un archivo nuevo
   `tests/test_cli.py`.

6. **Actualiza `README.md`** con la nueva sección del comando.

7. **Actualiza `CHANGELOG.md`** bajo `## [Unreleased]`.

8. **Sube la versión** en `pyproject.toml` y `autocomplete/__init__.py`
   si aplica (siguiendo SemVer).

9. **Commit y PR**.

---

## Cómo reportar un bug

Usa la plantilla de issue incluyendo:

- **Versión de Python** (`python --version`).
- **Sistema operativo** y versión.
- **Versión del paquete** (`pip show brayan-autocomplete` o
  `python -m autocomplete --version`).
- **Pasos para reproducir** (lo más concretos posible).
- **Comportamiento esperado** vs **comportamiento observado**.
- **Traza completa** si hay error.
- **Configuración relevante** (`python -m autocomplete config show`
  omitiendo datos sensibles).

### Ejemplo

```
Versión de Python: 3.13.7
SO: Windows 11
Versión del paquete: 1.5.0

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

Abre un issue con etiqueta `enhancement` y describe:

- **Problema** que resuelve.
- **Propuesta** concreta (API, comando, cambio de comportamiento).
- **Alternativas** consideradas.
- **Impacto** en compatibilidad.

Si el cambio es grande, espera aprobación antes de empezar a codificar.

---

## Pull requests

### Título

Sigue el mismo formato que los commits:

```
feat(daemon): añade autostart en primer Tab
```

### Descripción

Incluye:

- **Qué** cambia.
- **Por qué**.
- **Cómo probarlo** (comandos concretos).
- **Capturas** si es visual (no suele aplicar aquí).
- **Referencias** a issues (`Closes #42`).

### Revisión

- Un PR requiere al menos **una aprobación**.
- El CI debe pasar (tests + lint).
- Los comentarios de revisión deben resolverse antes del merge.

### Merge

- Se prefiere **squash and merge** para PRs pequeños.
- Para PRs grandes, merge normal.
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