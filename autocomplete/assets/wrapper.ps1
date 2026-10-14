# wrapper.ps1 - Tab wrapper daemon-aware
# Instalado por: autocomplete init
# O manualmente: . "$env:APPDATA\autocomplete\wrapper.ps1"

$script:AC_State = @{
    Index       = -1
    Prefix      = ""
    Suggestions = @()
}
$script:AC_PortFile = Join-Path $env:APPDATA "autocomplete\daemon.port"

function Reset-AutoCompleteState {
    $script:AC_State.Index = -1
    $script:AC_State.Prefix = ""
    $script:AC_State.Suggestions = @()
}

function Get-AutoCompleteDaemonPort {
    if (-not (Test-Path $script:AC_PortFile)) { return $null }
    try { return [int](Get-Content $script:AC_PortFile -Raw).Trim() } catch { return $null }
}

function Get-AutoCompleteFromDaemon {
    param([string]$Prefix, [int]$Limit = 20)
    $port = Get-AutoCompleteDaemonPort
    if (-not $port) { return $null }
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect("127.0.0.1", $port)
        $stream = $client.GetStream()
        $req = @{ op = "suggest"; prefix = $Prefix; limit = $Limit } | ConvertTo-Json -Compress
        $bytes = [Text.Encoding]::UTF8.GetBytes($req + "`n")
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush()

        $reader = New-Object System.IO.StreamReader($stream, [Text.Encoding]::UTF8)
        $line = $reader.ReadLine()
        $client.Close()
        if (-not $line) { return $null }
        $obj = $line | ConvertFrom-Json
        if (-not $obj.ok) { return $null }
        return ,@($obj.suggestions)
    } catch {
        return $null
    }
}

function Get-AutoCompleteFromCli {
    param([string]$Prefix, [int]$Limit = 20)
    try {
        $out = & python -m autocomplete suggest --limit $Limit $Prefix 2>$null
        if ($LASTEXITCODE -ne 0) { return @() }
        return ,@($out)
    } catch {
        return @()
    }
}

function Get-AutoCompleteSuggestions {
    param([string]$Prefix, [int]$Limit = 20)
    if ([string]::IsNullOrWhiteSpace($Prefix)) { return @() }
    $daemon = Get-AutoCompleteFromDaemon -Prefix $Prefix -Limit $Limit
    if ($null -ne $daemon) { return $daemon }
    return Get-AutoCompleteFromCli -Prefix $Prefix -Limit $Limit
}

Set-PSReadLineKeyHandler -Key Tab -ScriptBlock {
    $line = ""
    $cursor = 0
    [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]$line, [ref]$cursor)

    $before = $line.Substring(0, $cursor)
    $match = [regex]::Match($before, '(\S+)$')
    if (-not $match.Success) {
        [Microsoft.PowerShell.PSConsoleReadLine]::Insert("`t")
        return
    }

    $prefix = $match.Value
    $start = $match.Index

    if ($script:AC_State.Index -ge 0 -and $script:AC_State.Suggestions.Count -gt 0) {
        $currentWord = $line.Substring($start, [Math]::Min($cursor - $start, $line.Length - $start))
        $expected = $script:AC_State.Suggestions[$script:AC_State.Index]
        if ($currentWord -eq $expected -or $currentWord -eq $script:AC_State.Prefix) {
            $next = ($script:AC_State.Index + 1) % $script:AC_State.Suggestions.Count
            $script:AC_State.Index = $next
            $new = $script:AC_State.Suggestions[$next]
            $newLine = $before.Substring(0, $start) + $new + $line.Substring($cursor)
            $newCursor = $start + $new.Length
            [Microsoft.PowerShell.PSConsoleReadLine]::Replace(0, $line.Length, $newLine)
            [Microsoft.PowerShell.PSConsoleReadLine]::SetCursorPosition($newCursor)
            return
        }
    }

    $suggestions = @(Get-AutoCompleteSuggestions -Prefix $prefix)
    if ($suggestions.Count -eq 0) {
        [Microsoft.PowerShell.PSConsoleReadLine]::Insert("`t")
        return
    }

    $script:AC_State.Prefix = $prefix
    $script:AC_State.Suggestions = $suggestions
    $script:AC_State.Index = 0

    $new = $suggestions[0]
    $newLine = $before.Substring(0, $start) + $new + $line.Substring($cursor)
    $newCursor = $start + $new.Length
    [Microsoft.PowerShell.PSConsoleReadLine]::Replace(0, $line.Length, $newLine)
    [Microsoft.PowerShell.PSConsoleReadLine]::SetCursorPosition($newCursor)
}

Set-PSReadLineKeyHandler -Key Enter -ScriptBlock {
    Reset-AutoCompleteState
    [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
}

Write-Host "[autocomplete] Tab wrapper cargado (daemon-aware)." -ForegroundColor DarkGray