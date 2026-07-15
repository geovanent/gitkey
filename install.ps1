# gitkey installer - Windows (PowerShell)
# Keep this file ASCII-only so Windows PowerShell 5.1 can parse it without a UTF-8 BOM.
$ErrorActionPreference = "Stop"

$RepoUrl    = "git@github.com:geovanent/gitkey.git"
$InstallDir = Join-Path $env:USERPROFILE ".ssh\gitkey"
$BinDir     = Join-Path $env:USERPROFILE ".local\bin"
# Path is null when the script is piped into iex (iwr ... | iex)
$ScriptPath = $MyInvocation.MyCommand.Path
$RepoRoot   = if (-not [string]::IsNullOrWhiteSpace($ScriptPath)) {
    Split-Path -Parent $ScriptPath
} else {
    $null
}

function Write-Info($msg)  { Write-Host "-> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "OK $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "! $msg" -ForegroundColor Yellow }
function Write-Die($msg)   { Write-Host "X $msg" -ForegroundColor Red; exit 1 }

function Test-Python {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Die "Python 3.8+ is required. Install from python.org"
    }
    Write-Ok "Python is available"
}

function Test-App($dir) {
    return Test-Path (Join-Path $dir "lib\switch_profile.py")
}

function Ensure-Repo {
    if (Test-Path (Join-Path $InstallDir ".git")) {
        Write-Info "Updating $InstallDir..."
        Push-Location $InstallDir
        try { git pull --ff-only 2>$null } catch { git pull 2>$null }
        Pop-Location
    }
    elseif ($RepoRoot -and (Test-App $RepoRoot)) {
        Write-Info "Installing from $RepoRoot..."
        New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
        Copy-Item -Path "$RepoRoot\*" -Destination $InstallDir -Recurse -Force `
            -Exclude @(".git", "settings.py", "repo_bindings.json")
    }
    else {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Die "Git is required. Install Git for Windows."
        }
        Write-Info "Cloning into $InstallDir..."
        New-Item -ItemType Directory -Force -Path (Split-Path $InstallDir) | Out-Null
        git clone $RepoUrl $InstallDir
    }
}

function Setup-Settings {
    $example  = Join-Path $InstallDir "lib\settings-example.py"
    $settings = Join-Path $InstallDir "settings.py"
    if (-not (Test-Path $settings)) {
        Copy-Item $example $settings
        Write-Ok "Created $settings"
    }
    else {
        Write-Ok "Keeping existing $settings"
    }
}

function Link-Cli {
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    $cmdPath = Join-Path $BinDir "gitkey.cmd"
    $pyScript = Join-Path $InstallDir "lib\switch_profile.py"
    # Expand $pyScript here; leave %* for cmd.exe argument forwarding.
    $cmdBody = @"
@echo off
python "$pyScript" %*
"@
    Set-Content -Path $cmdPath -Value $cmdBody -Encoding ASCII
    Write-Ok "Created $cmdPath"
}

function Ensure-PathEnv {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -split ";" | Where-Object { $_ -eq $BinDir }) {
        Write-Ok "PATH already includes $BinDir"
        return
    }
    $newPath = if ($userPath) { "$BinDir;$userPath" } else { $BinDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$BinDir;$env:Path"
    Write-Ok "Added $BinDir to user PATH"
}

Test-Python | Out-Null
Ensure-Repo
Setup-Settings
Link-Cli
Ensure-PathEnv

Write-Host ""
Write-Ok "Installation complete"
Write-Host ""
Write-Host "  Edit $InstallDir\settings.py"
Write-Host "  Close and reopen the terminal (or restart Cursor), then run: gitkey"
Write-Host ""
Write-Host "  Until then you can run:"
Write-Host "  & `"$BinDir\gitkey.cmd`""
Write-Host ""
Write-Warn "Optional: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned"
Write-Warn "For full SSH support, prefer WSL or Git Bash with install.sh"
