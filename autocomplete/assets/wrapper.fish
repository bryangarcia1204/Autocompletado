# wrapper.fish - Tab completion daemon-aware para fish

function __ac_from_daemon
    set -l prefix $argv[1]
    set -l limit 20
    test (count $argv) -ge 2; and set limit $argv[2]
    set -l port_file "$XDG_CONFIG_HOME/autocomplete/daemon.port"
    test -f "$port_file"; or return 1
    command -q nc; or return 1
    set -l port (cat "$port_file" 2>/dev/null)
    test -n "$port"; or return 1
    set -l resp (printf '{"op":"suggest","prefix":"%s","limit":%d}\n' "$prefix" "$limit" \
        | nc -w 1 127.0.0.1 "$port" 2>/dev/null)
    test -n "$resp"; or return 1
    printf '%s' "$resp" | python -c \
        'import sys,json; print("\n".join(json.load(sys.stdin).get("suggestions") or []))' \
        2>/dev/null
end

function __ac_suggest
    set -l cur (commandline -ct)
    test -z "$cur"; and return
    set -l suggestions (__ac_from_daemon "$cur" 20)
    if test (count $suggestions) -eq 0
        set suggestions (python -m autocomplete suggest --limit 20 "$cur" 2>/dev/null)
    end
    for s in $suggestions
        printf '%s\n' "$s"
    end
end

complete -c '' -f -a '(__ac_suggest)'