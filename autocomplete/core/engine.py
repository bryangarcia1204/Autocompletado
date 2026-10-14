"""Autocompletador reutilizable basado en Trie."""

import gzip

from pathlib import Path
from typing import Callable, Iterable, List, Optional, TextIO, Tuple, Union, Dict

from .stats import LoadDirStats, LoadStats
from ..exceptions import InvalidPrefixError, InvalidWordError
from ..text.normalization import strip_accents
from .trie import Trie
from ..core.similarity import find_similar

# Tipos de entrada aceptados por bulk_load
FileSource = Union[str, Path, TextIO]




class Autocomplete:
    """Autocompletador basado en Trie.

    Ejemplo:
        >>> ac = Autocomplete()
        >>> ac.add_words(["casa", "casamiento", "casco"])
        >>> ac.suggestions("cas")
        ['casa', 'casamiento', 'casco']

    Ejemplo con acentos:
        >>> ac = Autocomplete(["café", "cafetería", "cama"])
        >>> ac.suggestions("cafe")     # encuentra 'café'
        ['café', 'cafetería']
    """

    def __init__(
        self,
        words: Optional[Iterable[str]] = None,
        remove_accents: bool = True,
    ) -> None:
        """
        Args:
            words: Iterable opcional de palabras iniciales.
            remove_accents: Si ``True`` (por defecto), las búsquedas
                ignoran acentos y mayúsculas.
        """
        self._trie = Trie(remove_accents=remove_accents)
        self._remove_accents = remove_accents
        if words:
            self.add_words(words)

    # ------------------------------------------------------------------ #
    # Constructores alternativos
    # ------------------------------------------------------------------ #
    @classmethod
    def from_file(
        cls,
        source: FileSource,
        *,
        encoding: str = "utf-8",
        separator: Optional[str] = None,
        comment_prefix: Optional[str] = "#",
        weight_column: int = 1,
        remove_accents: bool = True,
    ) -> "Autocomplete":
        """Crea una instancia cargando palabras desde un archivo.

        Ver :meth:`bulk_load` para los parámetros.
        """
        ac = cls(remove_accents=remove_accents)
        ac.bulk_load(
            source,
            encoding=encoding,
            separator=separator,
            comment_prefix=comment_prefix,
            weight_column=weight_column,
        )
        return ac

    # ------------------------------------------------------------------ #
    # API básica
    # ------------------------------------------------------------------ #
    def add_word(self, word: str, weight: int = 1) -> None:
        """Agrega una palabra al autocompletador.

        Args:
            word: Palabra a agregar.
            weight: Peso/frecuencia. Debe ser > 0.

        Raises:
            InvalidWordError: Si la palabra no es válida.
        """
        if not isinstance(word, str):
            raise InvalidWordError(
                f"Se esperaba str, se recibió {type(word).__name__}"
            )

        word = word.strip()
        if not word:
            raise InvalidWordError("La palabra no puede estar vacía")
        if weight <= 0:
            raise InvalidWordError("El peso debe ser mayor que cero")

        self._trie.insert(word, weight)

    def add_words(self, words: Iterable[str]) -> None:
        """Agrega múltiples palabras.

        Acepta un iterable o un dict ``{palabra: peso}``.
        """
        if isinstance(words, dict):
            for word, weight in words.items():
                self.add_word(word, weight)
            return

        for word in words:
            self.add_word(word)

    def remove_word(self, word: str) -> bool:
        """Elimina una palabra. Retorna ``True`` si existía."""
        if not isinstance(word, str) or not word.strip():
            raise InvalidWordError("La palabra a eliminar no es válida")
        return self._trie.remove(word.strip())

    def contains(self, word: str) -> bool:
        """Indica si la palabra exacta está registrada."""
        if not isinstance(word, str) or not word.strip():
            return False
        return self._trie.contains(word.strip())

    def all_words(self) -> Iterable[str]:
        """Itera todas las palabras almacenadas (palabra original)."""
        return self._trie.iter_words()

    def correct(
        self,
        word: str,
        max_distance: int = 2,
        limit: Optional[int] = 5,
    ) -> List[Tuple[str, int]]:
        """Sugiere correcciones para una palabra mal escrita.

        Usa distancia Damerau-Levenshtein (transposición cuenta como 1).

        Args:
            word: Palabra posiblemente mal escrita.
            max_distance: Distancia máxima aceptada.
            limit: Máximo de sugerencias (``None`` = sin límite).

        Returns:
            Lista de ``(palabra, distancia)`` ordenada por cercanía.
        """
        if not isinstance(word, str) or not word.strip():
            raise InvalidWordError("La palabra a corregir no es válida")
        return find_similar(
            word.strip(),
            self._trie.iter_words(),
            max_distance=max_distance,
            limit=limit,
            ignore_accents=self._remove_accents,
        )

    # ------------------------------------------------------------------ #
    # bulk_load
    # ------------------------------------------------------------------ #
    def bulk_load(
        self,
        source: FileSource,
        *,
        encoding: str = "utf-8",
        separator: Optional[str] = None,
        comment_prefix: Optional[str] = "#",
        weight_column: int = 1,
        on_progress: Optional[Callable[[int], None]] = None,
        progress_every: int = 10_000,
    ) -> LoadStats:
        """Carga masiva de palabras desde un archivo.

        Formatos soportados (autodetectados por sufijo):

        - ``.txt`` / ``.csv`` / ``.tsv`` / cualquier texto plano.
        - ``.gz`` (se descomprime automáticamente con ``gzip``).

        Estructura de cada línea:

        - Si ``separator is None``: una palabra por línea.
        - Si ``separator`` se especifica (p. ej. ``"\\t"`` o ``","``):
          la primera columna es la palabra y la columna ``weight_column``
          es el peso (entero). Si no hay peso, se asume ``1``.

        Las líneas vacías y las que empiezan por ``comment_prefix`` se
        omiten y se cuentan como ``skipped``.

        Args:
            source: Ruta al archivo, ``Path`` o un file-like ya abierto.
            encoding: Codificación de lectura (por defecto ``utf-8``).
            separator: Separador de columnas. ``None`` = una palabra por línea.
            comment_prefix: Prefijo de línea de comentario. ``None`` para desactivar.
            weight_column: Índice (0-based) de la columna con el peso.
            on_progress: Callback invocado cada ``progress_every`` líneas
                con el número de líneas procesadas hasta el momento.
            progress_every: Frecuencia del callback de progreso.

        Returns:
            :class:`LoadStats` con contadores y errores.
        """
        stats = LoadStats()
        stream, should_close = self._open_source(source, encoding)

        try:
            for line_num, raw in enumerate(stream, start=1):
                line = raw.rstrip("\n").rstrip("\r")
                stripped = line.strip()

                # Ignorar vacías y comentarios
                if not stripped:
                    stats.skipped += 1
                    continue
                if comment_prefix and stripped.startswith(comment_prefix):
                    stats.skipped += 1
                    continue

                try:
                    word, weight = self._parse_line(
                        stripped, separator, weight_column
                    )
                    if not word:
                        stats.skipped += 1
                        continue
                    self.add_word(word, weight=weight)
                    stats.loaded += 1
                except Exception as exc:  # noqa: BLE001
                    stats.skipped += 1
                    stats.errors.append(f"Línea {line_num}: {exc}")

                if (
                    on_progress is not None
                    and progress_every > 0
                    and line_num % progress_every == 0
                ):
                    on_progress(line_num)
        finally:
            if should_close:
                stream.close()

        return stats

    def bulk_load_dir(
        self,
        directory: Union[str, Path],
        *,
        pattern: str = "*.txt",
        recursive: bool = False,
        encoding: str = "utf-8",
        separator: Optional[str] = None,
        comment_prefix: Optional[str] = "#",
        weight_column: int = 1,
        on_progress: Optional[Callable[[Path, int], None]] = None,
        progress_every: int = 10_000,
    ) -> LoadDirStats:
        """Carga todos los archivos que coincidan con ``pattern`` dentro
        de ``directory``.

        Args:
            directory: Directorio a escanear.
            pattern: Patrón glob (por defecto ``"*.txt"``).
            recursive: Si ``True`` busca en subdirectorios con ``**``.
            encoding: Codificación de lectura.
            separator: Separador de columnas (igual que ``bulk_load``).
            comment_prefix: Prefijo de comentario.
            weight_column: Columna del peso.
            on_progress: Callback por archivo con (ruta, líneas leídas).
            progress_every: Frecuencia del callback dentro de cada archivo.

        Returns:
            :class:`LoadDirStats` con el detalle por archivo.
        """
        base = Path(directory)
        if not base.is_dir():
            raise FileNotFoundError(f"No es un directorio: {base}")

        glob = f"**/{pattern}" if recursive else pattern
        files = sorted(p for p in base.glob(glob) if p.is_file())

        stats = LoadDirStats()
        for path in files:
            file_stats = self.bulk_load(
                path,
                encoding=encoding,
                separator=separator,
                comment_prefix=comment_prefix,
                weight_column=weight_column,
                on_progress=(
                    (lambda n, p=path: on_progress(p, n))
                    if on_progress is not None
                    else None
                ),
                progress_every=progress_every,
            )
            stats.files[path.name] = file_stats
        return stats

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #
    @staticmethod
    def _open_source(
        source: FileSource, encoding: str
    ) -> Tuple[TextIO, bool]:
        """Abre la fuente. Devuelve (stream, debe_cerrarse)."""
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.suffix.lower() == ".gz":
                return gzip.open(path, "rt", encoding=encoding), True
            return open(path, "r", encoding=encoding), True
        return source, False

    @staticmethod
    def _parse_line(
        line: str,
        separator: Optional[str],
        weight_column: int,
    ) -> Tuple[str, int]:
        """Extrae palabra y peso de una línea."""
        if separator is None:
            return line, 1

        parts = [p.strip() for p in line.split(separator)]
        if not parts or not parts[0]:
            return "", 1

        word = parts[0]
        weight = 1
        if len(parts) > weight_column:
            raw_weight = parts[weight_column]
            if raw_weight:
                try:
                    weight = int(raw_weight)
                except ValueError as exc:
                    raise InvalidWordError(
                        f"peso inválido: {raw_weight!r}"
                    ) from exc
        return word, weight

    # ------------------------------------------------------------------ #
    # Búsqueda
    # ------------------------------------------------------------------ #
    def suggestions(
        self,
        prefix: str,
        limit: Optional[int] = None,
        sort_by_frequency: bool = True,
    ) -> List[str]:
        """Devuelve las sugerencias que comienzan con ``prefix``.

        La búsqueda ignora acentos y mayúsculas si ``remove_accents=True``.

        Args:
            prefix: Prefijo a buscar.
            limit: Número máximo de sugerencias (``None`` = sin límite).
            sort_by_frequency: Si ``True`` ordena por frecuencia descendente
                y desempata alfabéticamente. Si ``False``, alfabético puro.

        Returns:
            Lista de palabras sugeridas.

        Raises:
            InvalidPrefixError: Si ``prefix`` no es un str.
        """
        if not isinstance(prefix, str):
            raise InvalidPrefixError("El prefijo debe ser un str")

        prefix = prefix.strip()
        if not prefix:
            return []

        node = self._trie.find_node(prefix)
        if node is None:
            return []

        collected: List[Tuple[str, int]] = []
        stack = [node]
        while stack:
            current = stack.pop()
            collected.extend(current.words.items())
            stack.extend(current.children.values())

        if sort_by_frequency:
            collected.sort(
                key=lambda item: (-item[1], strip_accents(item[0].lower()))
            )
        else:
            collected.sort(key=lambda item: strip_accents(item[0].lower()))

        words = [word for word, _ in collected]
        return words[:limit] if limit is not None else words

    # ------------------------------------------------------------------ #
    # Dunders
    # ------------------------------------------------------------------ #
    def __len__(self) -> int:
        """Cantidad de palabras únicas almacenadas."""
        return sum(1 for _ in self._trie.iter_words())

    def __contains__(self, word: object) -> bool:
        return isinstance(word, str) and self.contains(word)