# wrapper.zsh - Tab completion daemon-aware para zsh

_ac_port_file="${XDG_CONFIG_HOME:-$HOME/.config}/autocomplete/daemon.port"

_ac_from_daemon() {
    local prefix="$1" limit="${2:-20}"
    [ -f "$_ac_port_file" ] || return 1
    command -v nc >/dev/null 2>&1 || return 1
    local port; port=$(cat "$_ac_port_file" 2>/dev/null)
    [ -n "$port" ] || return 1
    local resp
    resp=$(printf '{"op":"suggest","prefix":"%s","limit":%d}\n' "$prefix" "$limit" \
        | nc -w 1 127.0.0.1 "$port" 2>/dev/null) || return 1
    [ -n "$resp" ] || return 1
    printf '%s' "$resp" | python -c \
        'import sys,json; print("\n".join(json.load(sys.stdin).get("suggestions") or []))' \
        2>/dev/null
}

_ac_suggest() {
    local cur="${words[CURRENT]}"
    [ -z "$cur" ] && return 0
    local suggestions
    suggestions=$(_ac_from_daemon "$cur" 20)
    if [ -z "$suggestions" ]; then
        suggestions=$(python -m autocomplete suggest --limit 20 "$cur" 2>/dev/null)
    fi
    local -a items
    items=("${(@f)suggestions}")
    compadd -a items
}

autoload -Uz compinit && compinit -C
compdef _ac_suggest -first-