# Load environment variables from .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#].*?)=(.*)$') {
        Set-Item -Path "env:\$($matches[1])" -Value $matches[2]
    }
}

# Keep OpenClaw config + state scoped to THIS project so it never clashes
# with other OpenClaw projects or a global ~/.openclaw config.
#   OPENCLAW_HOME       -> project root; state (sessions, creds, token) lives in ./.openclaw
#   OPENCLAW_CONFIG_PATH -> the repo-tracked config, not the global one
$env:OPENCLAW_HOME = $PSScriptRoot
$env:OPENCLAW_CONFIG_PATH = Join-Path $PSScriptRoot "openclaw\openclaw.json"

# Put the project venv first on PATH so the agent's skills can call a plain
# `python` (OS-agnostic) and get this project's interpreter + dependencies.
$env:Path = (Join-Path $PSScriptRoot ".venv\Scripts") + [IO.Path]::PathSeparator + $env:Path

# Change to openclaw directory and run
cd openclaw
Write-Host "Starting OpenClaw Gateway (project-local config: $env:OPENCLAW_CONFIG_PATH)..." -ForegroundColor Green
openclaw gateway run
