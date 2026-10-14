# wrapper.bash - Tab completion daemon-aware para bash
# Instalado por: autocomplete init
# Manual:
#   echo '[ -f "$HOME/.config/autocomplete/wrapper.bash" ] && source "$HOME/.config/autocomplete/wrapper.bash"' >> ~/.bashrc
#   source ~/.bashrc
#
# Usa el daemon si está corriendo (latencia ~5-15 ms).
# Si no, cae al CLI (latencia ~150-300 ms).

# Ruta del archivo que contiene el puerto del daemon
_ac_port_file() {
    local base="${XDG_CONFIG_HOME:-$HOME/.config}"
    echo "$base/autocomplete/daemon.port"
}

# Consulta al daemon vía socket TCP usando Python (no depende de nc)
_ac_from_daemon() {
    local prefix="$1"
    local limit="${2:-20}"
    local port_file
    port_file="$(_ac_port_file)"
    [ -f "$port_file" ] || return 1

    python - "$prefix" "$limit" "$port_file" <<'PY' 2>/dev/null
import json
import socket
import sys

prefix, limit, port_file = sys.argv[1], int(sys.argv[2]), sys.argv[3]

try:
    with open(port_file, "r", encoding="utf-8") as f:
        port = int(f.read().strip())
except (OSError, ValueError):
    sys.exit(1)

try:
    with socket.create_connection(("127.0.0.1", port), timeout=0.3) as s:
        req = json.dumps({"op": "suggest", "prefix": prefix, "limit": limit})
        s.sendall((req + "\n").encode("utf-8"))
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
    data = json.loads(buf.decode("utf-8"))
except (OSError, json.JSONDecodeError):
    sys.exit(1)

if not data.get("ok"):
    sys.exit(1)

for word in data.get("suggestions") or []:
    print(word)
PY
}

# Fallback al CLI
_ac_from_cli() {
    local prefix="$1"
    local limit="${2:-20}"
    python -m autocomplete suggest --limit "$limit" "$prefix" 2>/dev/null
}

# Punto de entrada del completion
_ac_suggest() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    [ -z "$cur" ] && return 0

    local suggestions
    suggestions="$(_ac_from_daemon "$cur" 20)" || \
        suggestions="$(_ac_from_cli "$cur" 20)"

    [ -z "$suggestions" ] && return 0

    # -W divide por palabras; -o nospace evita añadir espacio tras completar
    COMPREPLY=($(compgen -W "$suggestions" -- "$cur"))
    compopt -o nospace 2>/dev/null
}

# Aplica a TODOS los comandos (efecto wrapper global)
complete -F _ac_suggest -D