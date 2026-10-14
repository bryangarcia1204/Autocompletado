"""Asistente `autocomplete init`: detecta shell, instala wrapper,
crea la BD, carga palabras y arranca el daemon."""

from __future__ import annotations

import os
import subprocess
import sys
from importlib.resources import files
from pathlib import Path
from typing import Optional

from ..config.settings import Config, config_dir

WRAPPERS = {
    "pwsh": "wrapper.ps1",
    "powershell": "wrapper.ps1",
    "bash": "wrapper.bash",
    "zsh": "wrapper.zsh",
    "fish": "wrapper.fish",
}


# ---------------------------------------------------------------------- #
# Detección de shell
# ---------------------------------------------------------------------- #
def detect_shell() -> str:
    if sys.platform == "win32":
        if os.environ.get("POWERSHELL_DISTRIBUTION_CHANNEL"):
            return "pwsh"
        if os.environ.get("PSModulePath"):
            return "powershell"
        if os.environ.get("SHELL"):
            return Path(os.environ["SHELL"]).name
        return "cmd"
    shell = os.environ.get("SHELL")
    if shell:
        return Path(shell).name
    return "bash"


def profile_path(shell: str) -> Optional[Path]:
    home = Path.home()
    if shell == "pwsh":
        return _query_ps_profile("pwsh")
    if shell == "powershell":
        return _query_ps_profile("powershell")
    if shell == "bash":
        return home / ".bashrc"
    if shell == "zsh":
        return home / ".zshrc"
    if shell == "fish":
        return home / ".config" / "fish" / "config.fish"
    return None


def _query_ps_profile(exe: str) -> Optional[Path]:
    try:
        out = subprocess.run(
            [exe, "-NoProfile", "-Command", "$PROFILE"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        line = out.stdout.strip().splitlines()[-1].strip() if out.stdout else ""
        return Path(line) if line else None
    except (OSError, subprocess.SubprocessError):
        return None


# ---------------------------------------------------------------------- #
# Instalación de wrappers
# ---------------------------------------------------------------------- #
def _wrapper_text(name: str) -> str:
    # CORREGIDO: los wrappers viven en autocomplete.assets
    return files("autocomplete.assets").joinpath(name).read_text(
        encoding="utf-8"
    )


def _append_line_once(profile: Path, line: str, comment: str) -> bool:
    profile.parent.mkdir(parents=True, exist_ok=True)
    existing = (
        profile.read_text(encoding="utf-8", errors="ignore")
        if profile.exists()
        else ""
    )
    if line in existing:
        return False
    with profile.open("a", encoding="utf-8") as f:
        f.write(f"\n# {comment}\n{line}\n")
    return True


def install_wrapper(shell: str) -> Optional[Path]:
    wrapper_name = WRAPPERS.get(shell)
    if wrapper_name is None:
        print(f"  Shell '{shell}' no soportado para instalación automática.")
        return None

    profile = profile_path(shell)
    if profile is None:
        print(f"  No pude detectar el perfil de {shell}.")
        return None

    target_dir = config_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / wrapper_name
    target.write_text(_wrapper_text(wrapper_name), encoding="utf-8")

    if shell == "fish":
        line = f"source {target}"
    elif shell in ("pwsh", "powershell"):
        line = f'. "{target}"'
    else:
        line = f'[ -f "{target}" ] && source "{target}"'

    added = _append_line_once(profile, line, "autocomplete wrapper")
    if added:
        print(f"  Wrapper instalado: {target}")
        print(f"  Añadido a        : {profile}")
    else:
        print(f"  El perfil ya tenía el wrapper: {profile}")
    return profile


# ---------------------------------------------------------------------- #
# Wizard
# ---------------------------------------------------------------------- #
def _ask(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        ans = input(f"{prompt} {suffix} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not ans:
        return default
    return ans in ("y", "yes", "s", "si", "sí")


def run_init(interactive: bool = True) -> int:
    print("== Asistente de configuración de autocomplete ==\n")

    shell = detect_shell()
    print(f"Shell detectado: {shell}")

    if interactive and not _ask(f"¿Usar '{shell}'?", default=True):
        shell = (
            input("Escribe el shell (bash/zsh/fish/pwsh/powershell): ")
            .strip()
            or shell
        )

    cfg = Config()
    print(f"\nConfiguración: {cfg.path}")

    # ---------- BD ----------
    url = cfg.db_url()
    print(f"Base de datos : {url}")

    if interactive and not _ask("¿Usar SQLite por defecto?"):
        custom = input(
            "URL SQLAlchemy (ej. postgresql+psycopg://user:pass@host/db): "
        ).strip()
        if custom:
            cfg.set("database_url", custom)
            url = custom

    # ---------- Preferencias ----------
    if interactive:
        if _ask("¿Autoejecutar correcciones sin preguntar? (NO recomendado)"):
            cfg.set("auto_execute", True)
            cfg.set("confirm_before_execute", False)
        else:
            cfg.set("auto_execute", False)
            cfg.set("confirm_before_execute", True)

    cfg.save()
    print("  Configuración guardada.")

    # ---------- Palabras iniciales ----------
    file_path: Optional[Path] = None
    if interactive:
        raw = input(
            "\nArchivo de palabras a cargar (vacío para omitir): "
        ).strip()
        if raw:
            file_path = Path(raw).expanduser()

    from ..storage.repository import Storage

    try:
        storage = Storage(cfg.db_url())
        print(f"  BD lista ({storage.word_count()} palabras actuales).")

        if file_path and file_path.exists():
            # CORREGIDO: import relativo correcto desde interfaces/
            from ..core.engine import Autocomplete

            ac = Autocomplete(
                remove_accents=bool(cfg.get("remove_accents", True))
            )
            stats = ac.bulk_load(file_path)
            storage.add_many(
                [(w, 1) for w in ac.all_words()], source=str(file_path)
            )
            print(
                f"  Cargadas {stats.loaded} palabras desde {file_path} "
                f"({stats.skipped} omitidas)."
            )
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] No pude inicializar la BD: {exc}")

    # ---------- Wrapper ----------
    if interactive:
        install = _ask(f"\n¿Instalar wrapper de Tab para {shell}?", default=True)
    else:
        install = True

    if install:
        profile = install_wrapper(shell)
        if profile is not None:
            if shell in ("pwsh", "powershell"):
                print(f"\n  Recarga el perfil con:  . \"{profile}\"")
            elif shell == "fish":
                print(f"\n  Recarga el perfil con:  source {profile}")
            else:
                print(f"\n  Recarga el perfil con:  source {profile}")

    # ---------- Daemon ----------
    if interactive:
        start = _ask("\n¿Arrancar daemon en background?", default=True)
    else:
        start = True

    if start:
        from ..server.daemon import start_background

        start_background()

    # ---------- Resumen ----------
    print("\n== Listo ==")
    print("Prueba:")
    print("  git<TAB>                     # sugerencias (daemon)")
    print("  autocomplete config show")
    print("  autocomplete daemon status")
    print("  autocomplete db history")
    return 0