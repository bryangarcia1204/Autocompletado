"""Interfaz de línea de comandos del módulo autocomplete."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from ..config.settings import Config
from ..core.engine import Autocomplete
from ..exceptions import AutocompleteError
from ..execution.runner import run_command
from ..storage.repository import Storage


# ---------------------------------------------------------------------- #
# Parser
# ---------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="autocomplete",
        description="Autocompletado, autocorrección y sugerencia de comandos.",
    )
    p.add_argument("-f", "--file", help="Archivo a cargar (.txt/.tsv/.gz).")
    p.add_argument("--encoding", default="utf-8")
    p.add_argument("--separator", default=None)
    p.add_argument("--db-url", default=None, help="URL SQLAlchemy.")
    p.add_argument("--no-db", action="store_true")
    p.add_argument("--no-accents", action="store_true")

    sub = p.add_subparsers(dest="command", required=True)

    # ---- suggest ----
    s = sub.add_parser("suggest", help="Sugiere palabras por prefijo.")
    s.add_argument("prefix")
    s.add_argument("--limit", type=int, default=10)

    # ---- correct ----
    c = sub.add_parser("correct", help="Corrige y opcionalmente ejecuta.")
    c.add_argument("word")
    c.add_argument("--max-distance", type=int, default=2)
    c.add_argument("--limit", type=int, default=10)
    c.add_argument("--rest", default="", help="Args extra al comando.")
    c.add_argument(
        "-x", "--execute", action="store_true",
        help="Ejecutar la mejor corrección.",
    )
    c.add_argument(
        "-y", "--yes", action="store_true",
        help="No preguntar antes de ejecutar.",
    )

    # ---- shell ----
    sh = sub.add_parser(
        "shell", help="Autocorrector interactivo con ejecución."
    )
    sh.add_argument("--limit", type=int, default=5)
    sh.add_argument("--max-distance", type=int, default=2)
    sh.add_argument(
        "-y", "--yes", action="store_true",
        help="Ejecutar sin preguntar.",
    )
    sh.add_argument(
        "--dry-run", action="store_true",
        help="Mostrar sin ejecutar.",
    )

    # ---- repl ----
    r = sub.add_parser("repl", help="Explorador interactivo (solo sugiere).")
    r.add_argument("--limit", type=int, default=10)

    # ---- load-dir ----
    ld = sub.add_parser(
        "load-dir",
        help="Carga todos los archivos de un directorio a la BD.",
    )
    ld.add_argument("directory", help="Directorio a escanear.")
    ld.add_argument("--pattern", default="*.txt")
    ld.add_argument("--recursive", action="store_true")
    ld.add_argument("--encoding", default="utf-8")
    ld.add_argument("--separator", default=None)
    ld.add_argument(
        "--replace", action="store_true",
        help="Borra las palabras de la BD antes de cargar.",
    )

    # ---- config ----
    cfg = sub.add_parser("config", help="Preferencias persistentes.")
    csub = cfg.add_subparsers(dest="config_cmd", required=True)
    csub.add_parser("show")
    csub.add_parser("path")
    csub.add_parser("reset")
    cs = csub.add_parser("set")
    cs.add_argument("key")
    cs.add_argument("value")

    # ---- db ----
    db = sub.add_parser("db", help="Operaciones sobre la base de datos.")
    dsub = db.add_subparsers(dest="db_cmd", required=True)

    dsub.add_parser("init", help="Inicializa la BD.")
    dsub.add_parser("info", help="Muestra información de la BD.")

    dadd = dsub.add_parser("add", help="Añade palabras.")
    dadd.add_argument("words", nargs="+")
    dadd.add_argument("--weight", type=int, default=1)

    drm = dsub.add_parser("remove", help="Elimina palabras.")
    drm.add_argument("words", nargs="+")

    dlist = dsub.add_parser("list", help="Lista palabras almacenadas.")
    dlist.add_argument("--limit", type=int, default=50)

    dhist = dsub.add_parser("history", help="Historial de comandos.")
    dhist.add_argument("--limit", type=int, default=20)
    dhist.add_argument(
        "--clear", action="store_true",
        help="Borra todo el historial.",
    )

    drs = dsub.add_parser(
        "restart",
        help="Reinicia la BD (borra todos los datos y recrea el esquema).",
    )
    drs.add_argument(
        "-y", "--yes", action="store_true",
        help="No pedir confirmación.",
    )

    dbk = dsub.add_parser(
        "backup",
        help="Genera un respaldo de la base de datos.",
    )
    dbk.add_argument(
        "-o", "--output", default=None,
        help="Ruta del archivo de salida (opcional).",
    )

    drst = dsub.add_parser(
        "restore",
        help="Restaura un respaldo previo.",
    )
    drst.add_argument(
        "input",
        help="Ruta del archivo de backup a restaurar.",
    )
    drst.add_argument(
        "-y", "--yes", action="store_true",
        help="No pedir confirmación.",
    )

    dvac = dsub.add_parser(
        "vacuum",
        help="Compacta la base de datos.",
    )

    # ---- daemon ----
    dm = sub.add_parser("daemon", help="Gestiona el daemon de sugerencias.")
    dmsub = dm.add_subparsers(dest="daemon_cmd", required=True)
    dsub_run = dmsub.add_parser("run", help="Corre en primer plano.")
    dsub_run.add_argument("--host", default="127.0.0.1")
    dsub_run.add_argument("--port", type=int, default=0)
    dmsub.add_parser("start", help="Arranca en background.")
    dmsub.add_parser("stop", help="Detiene el daemon.")
    dmsub.add_parser("status", help="Estado del daemon.")
    dmsub.add_parser("reload", help="Recarga palabras desde la BD.")
    dmsub.add_parser("restart", help="Reinicia el daemon.")

    # ---- init ----
    initp = sub.add_parser("init", help="Asistente de configuración.")
    initp.add_argument(
        "-y", "--yes", action="store_true", help="Sin preguntas."
    )

    # ---- install-ps ----
    sub.add_parser(
        "install-ps",
        help="Instala el wrapper de Tab en PowerShell.",
    )

    return p


# ---------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------- #
def _notify_daemon_reload() -> None:
    from ..server.client import DaemonClient

    c = DaemonClient(timeout=0.5)
    if c.ping():
        c.reload()


def _wrapper_resource(name: str) -> str:
    """Lee un wrapper desde ``autocomplete.assets``."""
    from importlib.resources import files

    return files("autocomplete.assets").joinpath(name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------- #
# Handlers auxiliares
# ---------------------------------------------------------------------- #
def handle_config(config: Config, args: argparse.Namespace) -> int:
    if args.config_cmd == "show":
        print(json.dumps(config.as_dict(), indent=2, ensure_ascii=False))
        return 0
    if args.config_cmd == "path":
        print(config.path)
        return 0
    if args.config_cmd == "reset":
        config.reset()
        config.save()
        print(f"Configuración reiniciada: {config.path}")
        return 0
    if args.config_cmd == "set":
        raw = args.value
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        config.set(args.key, value)
        config.save()
        print(f"{args.key} = {value!r}")
        return 0
    return 2


def handle_db(
    config: Config, args: argparse.Namespace, storage: Optional[Storage]
) -> int:
    if storage is None:
        print("Base de datos no disponible.", file=sys.stderr)
        return 2

    if args.db_cmd == "init":
        print(f"BD lista en {storage.url}")
        return 0

    if args.db_cmd == "info":
        print(f"URL           : {storage.url}")
        print(f"Motor         : {storage.dialect}")
        print(f"Palabras      : {storage.word_count()}")
        prefs = storage.all_prefs()
        print(f"Preferencias  : {len(prefs)}")
        size = storage.db_size_bytes()
        if size is not None:
            print(f"Tamaño        : {size / 1024:.1f} KB")
        return 0

    if args.db_cmd == "add":
        for w in args.words:
            storage.add_word(w, weight=args.weight, source="cli")
        print(f"Añadidas {len(args.words)} palabra(s).")
        _notify_daemon_reload()
        return 0

    if args.db_cmd == "remove":
        n = sum(1 for w in args.words if storage.remove_word(w))
        print(f"Eliminadas {n} palabra(s).")
        _notify_daemon_reload()
        return 0

    if args.db_cmd == "list":
        rows = storage.all_words()
        for text, weight in rows[: args.limit]:
            print(f"{text}\t{weight}")
        return 0

    if args.db_cmd == "history":
        if args.clear:
            n = storage.clear_history()
            print(f"Historial borrado ({n} entradas).")
            return 0
        for h in storage.recent_history(args.limit):
            print(
                f"{h.created_at}\t{h.command}\t"
                f"-> {h.corrected or '-'}\texit={h.exit_code}"
            )
        return 0

    if args.db_cmd == "restart":
        if not args.yes:
            try:
                answer = input(
                    "Esto BORRARÁ todos los datos (palabras, historial, "
                    "preferencias). ¿Continuar? [y/N] "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return 1
            if answer not in ("y", "yes", "s", "si", "sí"):
                print("Cancelado.")
                return 1

        storage.reset()
        print("Base de datos reiniciada.")
        _notify_daemon_reload()
        return 0

    if args.db_cmd == "backup":
        try:
            target = storage.backup(args.output)
        except (OSError, NotImplementedError) as exc:
            print(f"Error al respaldar: {exc}", file=sys.stderr)
            return 2
        size_kb = target.stat().st_size / 1024
        print(f"Backup creado: {target}  ({size_kb:.1f} KB)")
        return 0

    if args.db_cmd == "restore":
        src = Path(args.input).expanduser()
        if not src.exists():
            print(f"No existe el archivo: {src}", file=sys.stderr)
            return 2

        if not args.yes:
            try:
                answer = input(
                    f"Esto REEMPLAZARÁ la BD actual con '{src}'. "
                    "¿Continuar? [y/N] "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return 1
            if answer not in ("y", "yes", "s", "si", "sí"):
                print("Cancelado.")
                return 1

        try:
            storage.restore(str(src))
        except (OSError, NotImplementedError) as exc:
            print(f"Error al restaurar: {exc}", file=sys.stderr)
            return 2

        print(f"BD restaurada desde: {src}")
        print(f"Palabras actuales  : {storage.word_count()}")
        _notify_daemon_reload()
        return 0

    if args.db_cmd == "vacuum":
        try:
            storage.vacuum()
        except (OSError, NotImplementedError) as exc:
            print(f"Error al compactar: {exc}", file=sys.stderr)
            return 2

        size = storage.db_size_bytes()
        if size is not None:
            print(f"BD compactada. Tamaño actual: {size / 1024:.1f} KB")
        else:
            print("BD compactada.")
        return 0

    return 2


def handle_daemon(args: argparse.Namespace) -> int:
    # CORREGIDO: el daemon ahora vive en autocomplete.server
    from ..server import daemon as dm

    if args.daemon_cmd == "run":
        return dm.run_server(host=args.host, port=args.port)
    if args.daemon_cmd == "start":
        return dm.start_background()
    if args.daemon_cmd == "stop":
        return dm.stop_background()
    if args.daemon_cmd == "status":
        return dm.status()
    if args.daemon_cmd == "reload":
        from ..server.client import DaemonClient

        c = DaemonClient()
        if not c.ping():
            print("El daemon no está corriendo.", file=sys.stderr)
            return 1
        ok = c.reload()
        print("Recargado." if ok else "Error al recargar.", file=sys.stderr)
        return 0 if ok else 1
    if args.daemon_cmd == "restart":
        dm.stop_background()
        return dm.start_background()
    return 2


def handle_install_ps() -> int:
    # CORREGIDO: los wrappers viven en autocomplete.assets
    try:
        content = _wrapper_resource("wrapper.ps1")
    except FileNotFoundError:
        print(
            "wrapper.ps1 no encontrado en autocomplete.assets.",
            file=sys.stderr,
        )
        return 1

    from ..config.settings import config_dir

    target_dir = config_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "wrapper.ps1"
    target.write_text(content, encoding="utf-8")

    print(f"Wrapper instalado en: {target}")
    print()
    print("Añade esta línea a tu $PROFILE de PowerShell:")
    print(f'  . "{target}"')
    print()
    print("Para editar el perfil:")
    print("  notepad $PROFILE")
    print()
    print("Y recarga con:  . $PROFILE")
    return 0


# ---------------------------------------------------------------------- #
# Carga del Autocomplete
# ---------------------------------------------------------------------- #
def _build_autocomplete(
    args: argparse.Namespace,
    config: Config,
    storage: Optional[Storage],
) -> Autocomplete:
    ac = Autocomplete(remove_accents=not args.no_accents)

    if storage is not None:
        for text, weight in storage.all_words():
            ac.add_word(text, weight=weight)

    if args.file:
        stats = ac.bulk_load(
            args.file,
            encoding=args.encoding,
            separator=args.separator,
        )
        print(
            f"[autocomplete] {stats.loaded} del archivo, "
            f"{stats.skipped} omitidas.",
            file=sys.stderr,
        )
        if storage is not None:
            storage.add_many(
                [(w, 1) for w in ac.all_words()],
                source=str(args.file),
            )

    return ac


# ---------------------------------------------------------------------- #
# Subcomandos
# ---------------------------------------------------------------------- #
def cmd_suggest(ac: Autocomplete, args: argparse.Namespace) -> int:
    from ..server.client import DaemonClient

    client = DaemonClient()
    if client.ping():
        results = client.suggest(args.prefix, limit=args.limit) or []
    else:
        results = ac.suggestions(args.prefix, limit=args.limit)
    for word in results:
        print(word)
    return 0 if results else 1


def cmd_correct(
    ac: Autocomplete,
    args: argparse.Namespace,
    storage: Optional[Storage],
    config: Config,
) -> int:
    results = ac.correct(
        args.word, max_distance=args.max_distance, limit=args.limit
    )
    if not results:
        print(f"Sin sugerencias para '{args.word}'", file=sys.stderr)
        return 1

    for word, dist in results:
        print(f"{word}\t(distancia={dist})")

    if not args.execute:
        return 0

    best = results[0][0]
    full = f"{best} {args.rest}".strip() if args.rest else best

    auto = args.yes or bool(config.get("auto_execute"))
    if not auto and config.get("confirm_before_execute", True):
        try:
            answer = input(f"¿Ejecutar '{full}'? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1
        if answer not in ("", "y", "yes", "s"):
            print("Cancelado.")
            if storage:
                storage.add_history(
                    command=args.word, corrected=full, executed=False
                )
            return 1

    result = run_command(full, timeout=config.get("timeout"))
    if storage:
        storage.add_history(
            command=args.word,
            corrected=full if full != args.word else None,
            executed=True,
            exit_code=result.exit_code,
        )
    return result.exit_code


def cmd_repl(ac: Autocomplete, args: argparse.Namespace) -> int:
    print("Modo explorador. 'salir' o Ctrl+D para terminar.\n")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in {"salir", "exit", "quit"}:
            break

        suggestions = ac.suggestions(line, limit=args.limit)
        corrections = ac.correct(line, max_distance=2, limit=args.limit)
        seen = set(suggestions)
        extras = [(w, d) for w, d in corrections if w not in seen]

        if suggestions:
            print("  Sugerencias:")
            for s in suggestions:
                print(f"    - {s}")
        if extras:
            print("  Correcciones:")
            for w, d in extras:
                print(f"    - {w}  (distancia {d})")
        if not suggestions and not extras:
            print("  (sin resultados)")
    return 0


def cmd_shell(
    ac: Autocomplete,
    args: argparse.Namespace,
    storage: Optional[Storage],
    config: Config,
) -> int:
    auto = args.yes or bool(config.get("auto_execute"))
    print("# Autocorrector. 'salir' para terminar.")
    print(
        "# Modo: "
        + ("EJECUTA SIN PREGUNTAR" if auto else "pregunta antes de ejecutar")
    )

    while True:
        try:
            line = input("$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in {"salir", "exit", "quit"}:
            break

        parts = line.split(maxsplit=1)
        cmd = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        target = line
        corrected: Optional[str] = None

        if not ac.contains(cmd):
            corrections = ac.correct(
                cmd, max_distance=args.max_distance, limit=args.limit
            )
            if not corrections:
                print(f"  Comando desconocido: '{cmd}' (sin sugerencias).")
                continue

            best = corrections[0][0]
            target = f"{best} {rest}".strip() if rest else best
            corrected = target
            print(f"  Corrección: {target}")
            if len(corrections) > 1:
                others = ", ".join(w for w, _ in corrections[1:])
                print(f"  Otras     : {others}")

        if args.dry_run:
            print(f"  [dry-run] {target}")
            continue

        if not auto and config.get("confirm_before_execute", True):
            try:
                answer = input(
                    f"  ¿Ejecutar '{target}'? [Y/n] "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if answer not in ("", "y", "yes", "s"):
                print("  Cancelado.")
                if storage:
                    storage.add_history(
                        command=line, corrected=corrected, executed=False
                    )
                continue

        result = run_command(target, timeout=config.get("timeout"))
        if storage:
            storage.add_history(
                command=line,
                corrected=corrected,
                executed=True,
                exit_code=result.exit_code,
            )
    return 0


def cmd_load_dir(
    storage: Optional[Storage], args: argparse.Namespace
) -> int:
    if storage is None:
        print("Base de datos no disponible.", file=sys.stderr)
        return 2

    if args.replace:
        removed = 0
        for text, _ in storage.all_words():
            if storage.remove_word(text):
                removed += 1
        print(f"BD vaciada ({removed} palabras eliminadas).")

    ac = Autocomplete()
    try:
        stats = ac.bulk_load_dir(
            args.directory,
            pattern=args.pattern,
            recursive=args.recursive,
            encoding=args.encoding,
            separator=args.separator,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Archivos procesados: {stats.total_files}")
    for name, s in sorted(stats.files.items()):
        print(f"  {name:<28} +{s.loaded:<5} (-{s.skipped})")

    storage.add_many(
        [(w, 1) for w in ac.all_words()], source=str(args.directory)
    )

    print(
        f"\nTotal: {stats.loaded} palabras cargadas, "
        f"{stats.skipped} omitidas."
    )
    if stats.errors:
        print(f"Errores: {len(stats.errors)}", file=sys.stderr)
        for e in stats.errors[:10]:
            print(f"  {e}", file=sys.stderr)

    _notify_daemon_reload()
    return 0


# ---------------------------------------------------------------------- #
# Main
# ---------------------------------------------------------------------- #
def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = Config()

    # Comandos sin BD
    if args.command == "config":
        return handle_config(config, args)
    if args.command == "install-ps":
        return handle_install_ps()
    if args.command == "init":
        from .wizard import run_init

        return run_init(interactive=not args.yes)
    if args.command == "daemon":
        return handle_daemon(args)

    # Storage
    storage: Optional[Storage] = None
    if not args.no_db:
        url = args.db_url or config.db_url()
        try:
            storage = Storage(url)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[warn] BD no disponible ({url}): {exc}", file=sys.stderr
            )

    if args.command == "db":
        return handle_db(config, args, storage)

    if args.command == "load-dir":
        return cmd_load_dir(storage, args)

    try:
        ac = _build_autocomplete(args, config, storage)
    except (OSError, AutocompleteError) as exc:
        print(f"Error al cargar datos: {exc}", file=sys.stderr)
        return 2

    if args.command == "suggest":
        return cmd_suggest(ac, args)
    if args.command == "correct":
        return cmd_correct(ac, args, storage, config)
    if args.command == "repl":
        return cmd_repl(ac, args)
    if args.command == "shell":
        return cmd_shell(ac, args, storage, config)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())