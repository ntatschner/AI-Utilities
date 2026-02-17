# Claude Code Workflow Hook — Remote Installer (Windows PowerShell)
#
# Usage:
#   Invoke-WebRequest -Uri "https://raw.githubusercontent.com/ntatschner/ai-utilities/main/tools/claude-dev-workflow-hook/install-remote.ps1" -OutFile "$env:TEMP\install-remote.ps1"; & "$env:TEMP\install-remote.ps1" -Scope Global
#   Invoke-WebRequest -Uri "https://raw.githubusercontent.com/ntatschner/ai-utilities/main/tools/claude-dev-workflow-hook/install-remote.ps1" -OutFile "$env:TEMP\install-remote.ps1"; & "$env:TEMP\install-remote.ps1" -Scope Project
#
# Downloads session-start.py and install.py to a temp directory, then runs the installer.

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("Global", "Project")]
    [string]$Scope
)

$ErrorActionPreference = "Stop"

$RepoBase = "https://raw.githubusercontent.com/ntatschner/ai-utilities/main/tools/claude-dev-workflow-hook"
$TmpDir = Join-Path $env:TEMP "claude-workflow-hook-$(Get-Random)"

try {
    New-Item -ItemType Directory -Path $TmpDir -Force | Out-Null

    Write-Host "Downloading workflow hook files..."
    Invoke-WebRequest -Uri "$RepoBase/session-start.py" -OutFile "$TmpDir\session-start.py"
    Invoke-WebRequest -Uri "$RepoBase/install.py" -OutFile "$TmpDir\install.py"

    # Detect Python
    $Python = $null
    foreach ($cmd in @("py", "python3", "python")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            $Python = $cmd
            break
        }
    }

    if (-not $Python) {
        Write-Host "ERROR: Python 3 not found. Install from https://www.python.org/downloads/" -ForegroundColor Red
        exit 1
    }

    Write-Host "Running installer with $Python..."

    $Args = @("$TmpDir\install.py")
    if ($Scope -eq "Global") {
        $Args += "--global"
    } elseif ($Scope -eq "Project") {
        $Args += "--project"
    }

    & $Python @Args
}
finally {
    if (Test-Path $TmpDir) {
        Remove-Item -Recurse -Force $TmpDir
    }
}
