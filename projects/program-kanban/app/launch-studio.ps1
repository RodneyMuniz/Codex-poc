param(
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"

function Get-HttpStatus {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return [int]$response.StatusCode
    } catch {
        return $null
    }
}

function Get-ListeningProcessId {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        return $connection.OwningProcess
    } catch {
        return $null
    }
}

function Start-AppProcess {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$App
    )

    $statusCode = Get-HttpStatus -Url $App.Url
    if ($statusCode) {
        return [ordered]@{
            name = $App.Name
            url = $App.Url
            port = $App.Port
            state = "already_running"
            status_code = $statusCode
            pid = Get-ListeningProcessId -Port $App.Port
            stdout_log = $App.StdOut
            stderr_log = $App.StdErr
        }
    }

    $process = Start-Process -FilePath $App.FilePath `
        -ArgumentList $App.ArgumentList `
        -WorkingDirectory $App.WorkingDirectory `
        -RedirectStandardOutput $App.StdOut `
        -RedirectStandardError $App.StdErr `
        -WindowStyle Hidden `
        -PassThru

    Start-Sleep -Seconds $App.StartDelaySeconds
    $statusCode = Get-HttpStatus -Url $App.Url

    return [ordered]@{
        name = $App.Name
        url = $App.Url
        port = $App.Port
        state = $(if ($statusCode) { "started" } else { "starting" })
        status_code = $statusCode
        pid = $(if ($statusCode) { Get-ListeningProcessId -Port $App.Port } else { $process.Id })
        stdout_log = $App.StdOut
        stderr_log = $App.StdErr
    }
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot "..\..\.."))
$runtimeLogDir = Join-Path $workspaceRoot "sessions\runtime_logs"
$statusPath = Join-Path $scriptRoot "offline-launcher.status.json"

New-Item -ItemType Directory -Force -Path $runtimeLogDir | Out-Null

$programKanbanDir = $scriptRoot
$tacticsDir = Join-Path $workspaceRoot "projects\tactics-game\app"

$apps = @(
    @{
        Name = "Program Kanban"
        Url = "http://localhost:4187"
        Port = 4187
        FilePath = "powershell.exe"
        ArgumentList = @(
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Set-Location '$programKanbanDir'; node server.mjs"
        )
        WorkingDirectory = $programKanbanDir
        StdOut = Join-Path $runtimeLogDir "program-kanban.out.log"
        StdErr = Join-Path $runtimeLogDir "program-kanban.err.log"
        StartDelaySeconds = 2
    }
    @{
        Name = "TacticsGame"
        Url = "http://127.0.0.1:4173"
        Port = 4173
        FilePath = "cmd.exe"
        ArgumentList = @(
            "/c",
            "npm run dev -- --host 127.0.0.1 --port 4173"
        )
        WorkingDirectory = $tacticsDir
        StdOut = Join-Path $runtimeLogDir "tactics-game.out.log"
        StdErr = Join-Path $runtimeLogDir "tactics-game.err.log"
        StartDelaySeconds = 4
    }
)

$results = foreach ($app in $apps) {
    Start-AppProcess -App $app
}

$payload = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    workspace_root = $workspaceRoot
    launcher_root = $scriptRoot
    apps = $results
}

$payload | ConvertTo-Json -Depth 6 | Set-Content -Path $statusPath -Encoding UTF8

if ($OpenBrowser) {
    foreach ($app in $results) {
        if ($app.status_code) {
            Start-Process $app.url | Out-Null
        }
    }
}

$payload | ConvertTo-Json -Depth 6
